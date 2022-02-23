import re
import tempfile
import subprocess
from typing import List, Tuple

from git import Repo, Commit

REPO_URL = "git@github.com:TimJentzsch/stonefish_engine.git"

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


def process_repo(repo_url: str) -> None:
    organization, repository = get_organization_repository(repo_url)

    with tempfile.TemporaryDirectory() as tempdir:
        print(f"Cloning {organization}/{repository} to file://{tempdir}...")
        repo = Repo.clone_from(repo_url, tempdir)

        # Get the commits to process
        commits: List[Commit] = []
        for commit, _ in zip(repo.iter_commits(), range(20)):
            commits.append(commit)

        for commit in reversed(commits):
            print(
                "Processing ",
                GITHUB_COMMIT_URL.format(
                    organization=organization, repository=repository, hash=commit.hexsha
                ),
            )
            errors = check_compile_errors(tempdir)
            if errors:
                print("Errors detected!")
            else:
                print("No errors detected.")


def main():
    process_repo(REPO_URL)


if __name__ == "__main__":
    main()
