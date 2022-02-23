import tempfile
import subprocess

from git import Repo

REPO_URL = "git@github.com:TimJentzsch/stonefish_engine.git"


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


def process_repo(name: str, repo_url: str) -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        print(f"Cloning {name} to file://{tempdir}...")
        repo = Repo.clone_from(repo_url, tempdir)
        print(f"Active branch: {repo.active_branch} Dir: {repo.working_dir}")
        errors = check_compile_errors(tempdir)
        if errors:
            print("Errors detected!")
        else:
            print("No errors detected.")


def main():
    process_repo("Repo", REPO_URL)


if __name__ == "__main__":
    main()
