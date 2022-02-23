import subprocess
from typing import Union

ICE_TEXT = "error: internal compiler error: unexpected panic"

ProcessOutput = Union[subprocess.CompletedProcess, subprocess.CompletedProcess[str]]


def cargo_build(dir_path: str) -> ProcessOutput:
    """Run `cargo build` in the given directory."""
    return subprocess.run(
        ["cargo", "build"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=dir_path,
    )


def cargo_clean(dir_path: str) -> ProcessOutput:
    """Run `cargo clean` in the given directory."""
    return subprocess.run(
        ["cargo", "clean"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=dir_path,
    )


def check_for_ice(dir_path: str) -> bool:
    """Check for an internal compiler error (ICE) in the given directory."""
    build_output = cargo_build(dir_path)
    return build_output.returncode != 0 and (
        ICE_TEXT in build_output.stdout or ICE_TEXT in build_output.stderr
    )
