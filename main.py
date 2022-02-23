import re
import tempfile
from math import ceil
from typing import List, Tuple
import yaml

from git import Repo, Commit

from cargo import cargo_build, check_for_ice, cargo_clean

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


def process_repo(cfg, repo_url: str) -> bool:
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
        cargo_build(cfg, tempdir)

        print(f"Progress: 0/{len(commits)} (0%)")

        for batch in range(ceil(len(commits) / COMMIT_BATCH_COUNT)):
            batch_start = batch * COMMIT_BATCH_COUNT
            batch_end = batch_start + COMMIT_BATCH_COUNT

            for commit in commits[batch_start:batch_end]:
                repo.git.checkout(commit.hexsha)
                errors = check_for_ice(cfg, tempdir)
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
                    cargo_clean(cfg, tempdir)

            cur_count = min(len(commits), batch_end)
            percentage = cur_count / len(commits)
            print(f"Progress: {cur_count}/{len(commits)} ({percentage:.0%})")

    return found_error


def main():
    with open("config.yml", "r") as stream:
        try:
            cfg = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print(f"Failed to parse config.yml: {e}")
            exit(1)

    repos = cfg.get("repositories")
    if repos is None or len(repos) == 0:
        print(f"No repositories defined in config.yml!")
        exit(1)

    error_count = 0

    for repo in repos:
        if process_repo(cfg, repo):
            error_count += 1

    if error_count > 0:
        print(f"Found {error_count} internal compiler error(s).")
        exit(1)
    else:
        print(f"No internal compiler error found.")
        exit(0)


if __name__ == "__main__":
    main()
