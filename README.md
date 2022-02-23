# Rust Compiler Test

This tool attempts to find internal compiler errors (ICEs) for Rust by 
incrementally compiling the commit history of popular repositories.

## Installation

1. First, you'll need to install Git, Cargo, Python and Poetry.
2. Clone the repository.
3. Use `poetry install` to install the dependencies.

## Configuration

Create a `config.yml` file in the project root:

```yml
# Options for the cargo commands
cargo:
  # The toolchain to use for all cargo commands
  # toolchain: beta
  
  # Environment variables for cargo commands
  env:
      RUSTC_FORCE_INCREMENTAL: 1

# The repositories that should be tested
# They need to be GitHub SSH URLs for now
repositories:
  - git@github.com:bevyengine/bevy.git
```

## Usage

1. Run `python rust_ice_detector/main.py`.
2. Lean back and relax. This will take a while.
