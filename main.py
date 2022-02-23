import re
import tempfile
import subprocess
from math import ceil
from typing import List, Tuple

from git import Repo, Commit

REPO_URL = "git@github.com:TimJentzsch/stonefish_engine.git"
# REPO_URL = "git@github.com:bevyengine/bevy.git"

COMMIT_COUNT = 500
COMMIT_BATCH_COUNT = 20

GITHUB_SSH_REGEX = re.compile(
    r"^git@github\.com:(?P<organization>[\w_-]+)/(?P<repository>[\w_-]+)\.git$"
)
GITHUB_COMMIT_URL = "https://github.com/{organization}/{repository}/commit/{hash}"


def get_organization_repository(repo_url: str) -> Tuple[str, str]:
    """Extract the organization and repository from a repository URL."""
    match = GITHUB_SSH_REGEX.match(repo_url)
    if not match:
        print(f"Invalid repository URL '{repo_url}'. Please use a GitHub SSH URL.")
        exit(1)
    return match["organization"], match["repository"]


def check_compile_errors(dir_path: str) -> bool:
    """Checks for compile errors in the given directory.

    This will run `cargo build` and check for any errors in the output.
    """
    output = subprocess.run(
        ["cargo", "build"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=dir_path,
    )
    return output.returncode != 0


def process_repo(repo_url: str) -> bool:
    organization, repository = get_organization_repository(repo_url)

    found_error = False

    with tempfile.TemporaryDirectory() as tempdir:
        print(f"Cloning {organization}/{repository} to file://{tempdir}...")
        repo = Repo.clone_from(repo_url, tempdir)

        # Get the commits to process
        commits: List[Commit] = []
        for commit, _ in zip(repo.iter_commits(), range(COMMIT_COUNT)):
            commits.append(commit)
        commits.reverse()

        print("Compiling initial commit:")
        repo.git.checkout(commits[0].hexsha)
        check_compile_errors(tempdir)

        print(f"Progress: 0/{len(commits)} (0%)")

        for batch in range(ceil(len(commits) / COMMIT_BATCH_COUNT)):
            batch_start = batch * COMMIT_BATCH_COUNT
            batch_end = batch_start + COMMIT_BATCH_COUNT

            for commit in commits[batch_start:batch_end]:
                repo.git.checkout(commit.hexsha)
                errors = check_compile_errors(tempdir)
                if errors:
                    found_error = True
                    print(
                        "Error detected for ",
                        GITHUB_COMMIT_URL.format(
                            organization=organization,
                            repository=repository,
                            hash=commit.hexsha,
                        ),
                    )

            cur_count = min(len(commits), batch_end)
            percentage = cur_count / len(commits)
            print(f"Progress: {cur_count}/{len(commits)} ({percentage:.0%})")

    return found_error


def main():
    found_error = process_repo(REPO_URL)

    if found_error:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
