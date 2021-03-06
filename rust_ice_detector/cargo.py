import logging
import os
import subprocess
from typing import Union, Mapping

# Text to indicate an internal compiler error (ICE)
ICE_TEXT = "error: internal compiler error: unexpected panic"

# Snippets of expected error messages
# If an error message does NOT include one of this snippets, the tool will abort
EXPECTED_ERRORS = ["error: could not compile", "failed to load source for dependency"]

ProcessOutput = Union[subprocess.CompletedProcess, subprocess.CompletedProcess[str]]


def _get_cargo_env(cfg) -> Mapping[str, str]:
    """Get the environment to run cargo in.

    This command combines the OS environment with the custom env variables defined
    in cargo.env in the config file.
    """
    os_env = os.environ.copy()
    cargo_env = cfg.get("cargo", {}).get("env", {})
    cargo_env = {str(key): str(value) for key, value in cargo_env.items()}
    env = {
        **os_env,
        **cargo_env,
    }
    return env


def _is_expected_error(error: ProcessOutput) -> bool:
    """Determine if the given error is expected.

    If not, the tool should abort and exit.
    """
    error_message = error.stderr or error.stdout

    for snippet in EXPECTED_ERRORS:
        if snippet in error_message:
            return True

    return False


def _run_cargo_command(cfg, dir_path: str, cmd: str) -> ProcessOutput:
    """Run the given cargo command in the given directory."""
    env = _get_cargo_env(cfg)

    args = ["cargo"]

    # Add toolchain if specified
    if toolchain := cfg.get("cargo", {}).get("toolchain"):
        args.append(f"+{toolchain}")

    # Add actual command
    args.append(cmd)

    # Run the command
    output = subprocess.run(
        args,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=dir_path,
    )

    # Check if an unexpected error occurred
    # This could be e.g. an invalid toolchain
    # Normal compiler errors and ICEs are passed through
    if output.returncode != 0:
        if not _is_expected_error(output):
            logging.error("An unexpected error occurred:")
            logging.error(output.stdout)
            exit(1)
    return output


def cargo_build(cfg, dir_path: str) -> ProcessOutput:
    """Run `cargo build` in the given directory."""
    output = _run_cargo_command(cfg, dir_path, "build")
    return output


def cargo_check(cfg, dir_path: str) -> ProcessOutput:
    """Run `cargo check` in the given directory."""
    output = _run_cargo_command(cfg, dir_path, "check")
    return output


def cargo_clean(cfg, dir_path: str) -> ProcessOutput:
    """Run `cargo clean` in the given directory."""
    return _run_cargo_command(cfg, dir_path, "clean")


def check_for_ice(cfg, dir_path: str) -> bool:
    """Check for an internal compiler error (ICE) in the given directory."""
    output = cargo_check(cfg, dir_path)
    return output.returncode != 0 and (ICE_TEXT in (output.stderr or output.stdout))
