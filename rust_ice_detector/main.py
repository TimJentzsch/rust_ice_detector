import re
import sys
import tempfile
from math import ceil
from typing import List, Tuple
import yaml
import logging

from git import Repo, Commit

from cargo import cargo_build, check_for_ice, cargo_clean

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

GITHUB_SSH_REGEX = re.compile(
    r"^git@github\.com:(?P<organization>[\w_-]+)/(?P<repository>[\w_-]+)\.git$"
)
GITHUB_COMMIT_URL = "https://github.com/{organization}/{repository}/commit/{hash}"


def get_organization_repository(repo_url: str) -> Tuple[str, str]:
    """Extract the organization and repository from a repository URL."""
    match = GITHUB_SSH_REGEX.match(repo_url)
    if not match:
        logging.error(
            f"Invalid repository URL '{repo_url}'. Please use a GitHub SSH URL."
        )
        exit(1)
    return match["organization"], match["repository"]


def process_commit(
    cfg, dir_path: str, repo: Repo, commit: Commit, organization: str, repository: str
) -> bool:
    """Process a single commit by compiling and checking for errors.

    :returns: True, if an ICE was detected, else False.
    """
    # Check for errors
    repo.git.checkout(commit.hexsha)
    errors = check_for_ice(cfg, dir_path)

    if errors:
        logging.warning(
            "Error detected for ",
            GITHUB_COMMIT_URL.format(
                organization=organization,
                repository=repository,
                hash=commit.hexsha,
            ),
        )
        cargo_clean(cfg, dir_path)
        return True

    return False


def process_repo(cfg, repo_url: str) -> bool:
    organization, repository = get_organization_repository(repo_url)

    commit_count = cfg.get("commit_count", 100)
    commit_batch_size = cfg.get("commit_batch_size", 20)

    found_error = False

    with tempfile.TemporaryDirectory() as tempdir:
        logging.info(f"Cloning {organization}/{repository} to file://{tempdir}...")
        repo = Repo.clone_from(repo_url, tempdir)

        # Get the commits to process
        commits: List[Commit] = []
        for commit, _ in zip(repo.iter_commits(), range(commit_count)):
            commits.append(commit)
        commits.reverse()

        logging.info("Compiling initial commit...")
        repo.git.checkout(commits[0].hexsha)
        cargo_clean(cfg, tempdir)
        cargo_build(cfg, tempdir)

        logging.info(f"Progress: 0/{len(commits)} (0%)")

        for batch in range(ceil(len(commits) / commit_batch_size)):
            batch_start = batch * commit_batch_size
            batch_end = batch_start + commit_batch_size

            for commit in commits[batch_start:batch_end]:
                process_commit(cfg, tempdir, repo, commit, organization, repository)

            cur_count = min(len(commits), batch_end)
            percentage = cur_count / len(commits)
            logging.info(f"Progress: {cur_count}/{len(commits)} ({percentage:.0%})")

    return found_error


def main():
    with open("config.yml", "r") as stream:
        try:
            cfg = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            logging.error(f"Failed to parse config.yml: {e}")
            exit(1)

    repos = cfg.get("repositories")
    if repos is None or len(repos) == 0:
        logging.error(f"No repositories defined in config.yml!")
        exit(1)

    error_count = 0

    for repo in repos:
        if process_repo(cfg, repo):
            error_count += 1

    if error_count > 0:
        logging.warning(f"Found {error_count} internal compiler error(s).")
        exit(1)
    else:
        logging.info(f"No internal compiler error found.")
        exit(0)


if __name__ == "__main__":
    main()
