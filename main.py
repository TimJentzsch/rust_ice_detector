import tempfile

from git import Repo

REPO_URL = "git@github.com:TimJentzsch/stonefish_engine.git"


def process_repo(name: str, repo_url: str) -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        print(f"Cloning {name} to file://{tempdir}...")
        repo = Repo.clone_from(repo_url, tempdir)
        print(f"Active branch: {repo.active_branch}")


def main():
    process_repo("Repo", REPO_URL)


if __name__ == '__main__':
    main()
