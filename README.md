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

# The number of commits to compile for each repository
commit_count: 500
# The number of commits to compile before displaying a progress-update
commit_batch_size: 20

# The repositories that should be tested
# They need to be GitHub SSH URLs for now
repositories:
  - git@github.com:tauri-apps/tauri.git
  - git@github.com:tokio-rs/tokio.git
  - git@github.com:actix/actix-web.git
  - git@github.com:bevyengine/bevy.git
```

## Usage

1. Run `python rust_ice_detector/main.py`.
2. Lean back and relax. This will take a while.

## How it works

1. The tool clones the repositories to your temp folder.
2. It trances the most recent commits according to your configuration.
3. It builds the first commit.
4. It sequentially uses `cargo check` on the following commits.
5. If an internal compiler error (ICE) is detected, the link to the commit is logged.

## License

This project is licensed under [MIT](./LICENSE_MIT) and [Apache 2.0](./LICENSE_APACHE-2.0).
