# Local Development Instructions

To install the `ethstaker-deposit-cli`, follow these steps:

## Prerequisites

Ensure you have the following software installed on your system:

- **Git**: Version control system to clone the repository. [Download Git](https://git-scm.com/downloads)
- **Supported Python version**: The required version is declared in `pyproject.toml`. [Download Python](https://www.python.org/downloads/)
- **pip**: Package installer for Python, which is included with Python 3.

On Windows, you'll need:
- **Git for Windows**: Version control system to clone the repository. Configure it to associate `.sh` files with `bash`. [Download GfW](https://git-scm.com/download/win)
- **Windows Terminal**: Optional but recommended command line console. Configure GfW to install a Git Bash profile. [Download Windows Terminal](https://apps.microsoft.com/detail/9n0dx20hk701)
- **Supported Python version**: The required version is declared in `pyproject.toml`. [Download Python](https://apps.microsoft.com/detail/9ncvdn91xzqp)
- **Visual Studio C++**: The compiler required to build some of the dependencies of the tool. [Download VS C++](https://visualstudio.microsoft.com/vs/features/cplusplus/)

## Local Development Steps

1. **Clone the Repository**

    ```sh
    git clone https://github.com/ethstaker/ethstaker-deposit-cli.git
    ```

2. **Navigate to the Project Directory**

    ```sh
    cd ethstaker-deposit-cli
    ```

3. **Setup virtualenv (optional)**

    Install `venv` if not already installed, e.g. for Debian/Ubuntu:

    ```sh
    sudo apt update && sudo apt install python3-venv
    ```

    Create a new [virtual environment](https://docs.python.org/3/library/venv.html):

    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```

4. **Install Dependencies**

    ```sh
    python3 -m pip install -r requirements.txt
    ```

5. **Run the CLI**

    You can now run the CLI tool using the following command:

    ```sh
    python3 -m ethstaker_deposit [OPTIONS] COMMAND [ARGS]
    ```

6. **Use pre-commit for PRs**

    Install `pre-commit` if not already installed, e.g. for Debian/Ubuntu:

    ```sh
    sudo apt update && sudo apt install pre-commit
    ```

    Enable it for your `git commit` workflow:
    ```sh
    pre-commit install
    ```

    If you are using `uv`, you can also install it using:

    ```console
    uv sync --all-extras
    uv run pre-commit install
    ```

**To execute tests, you will need to install the test dependencies**:
```sh
python3 -m pip install -r requirements.txt -r requirements_test.txt
python3 -m pytest tests
```

## Building Local Binaries

The standalone binary targets use the Python version pinned by the `.github/workflows/build.yml` build step.

Build a Linux or macOS binary with:

```sh
make build_linux
make build_macos
```

These targets look for `python3.<xx>` matching the current build Python version, create or reuse the `venv/` environment with that interpreter, and install the pinned build dependencies. If an existing `venv/` was created with another Python version, it is recreated automatically.

If Python is installed under a non-standard path, provide it explicitly:

```sh
make BUILD_PYTHON=/path/to/python3.<xx> build_linux
```

The general development targets, such as `venv_test` and `venv_lint`, use `python3` by default. That interpreter must satisfy the `requires-python` range in `pyproject.toml`; override it with `PYTHON` when needed:

```sh
make PYTHON=python3.15 venv_test
```

The official release workflow builds binaries with a Python version pinned in `.github/workflows/build.yml`. Windows binaries are built by GitHub Actions using `build_configs/windows/build.spec`.

## Testing Built Binaries

The `binary_tests/` directory contains release-asset tests for the compiled `deposit` binary. Most drive the binary over a PTY with `expect` (a fully interactive happy path per CLI command, plus general TTY checks) and require `expect` on `PATH` (`sudo apt install expect` on Debian/Ubuntu, `brew install expect` on macOS); they replace the old root-level `test_binary_*.py` scripts. `binary_tests/test_non_interactive.sh` instead covers the expect-free `--non_interactive` flow (exit code and output file only), so it also runs on Windows.

Build a binary and run the whole suite against it:

```sh
make binary_test
```

This builds a standalone binary (via `build_linux`/`build_macos`, output in `./dist`) and then runs the release-asset tests against it: `binary_tests/run_tests.sh` (the interactive, expect-driven suite) and `binary_tests/test_non_interactive.sh` (the expect-free `--non_interactive` flow).

To test an existing build output (e.g. an unpacked release archive) without rebuilding:

```sh
bash binary_tests/run_tests.sh ./dist
bash binary_tests/run_tests.sh -s new_mnemonic ./dist   # a single test
bash binary_tests/run_tests.sh -l                        # list the available tests
```

The same suite can be run through tox against a pre-built binary:

```sh
make build_linux          # or make build_macos
tox -e binary-test
BINARY_TEST_BINARY_DIR=/path/to/binary-dir tox -e binary-test
```

In CI the suite runs on the Linux and macOS `ci-build` matrix entries as part of the release build workflow (`.github/workflows/build.yml`); Windows release assets are covered there by the `--version` smoke test and the `binary_tests/test_non_interactive.sh` check, which needs no expect.
