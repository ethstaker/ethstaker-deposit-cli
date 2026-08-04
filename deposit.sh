#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_VENV="$SCRIPT_DIR/.venv"

select_venv_python() {
    local venv_path="$1"
    local candidate

    for candidate in \
        "$venv_path/bin/python" \
        "$venv_path/bin/python3" \
        "$venv_path/Scripts/python.exe" \
        "$venv_path/Scripts/python"; do
        if [[ -x "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    return 1
}

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    if ! PYTHON=$(select_venv_python "$VIRTUAL_ENV"); then
        printf 'The active virtual environment has no usable Python interpreter: %s\n' "$VIRTUAL_ENV" >&2
        exit 1
    fi
elif PYTHON=$(select_venv_python "$PROJECT_VENV"); then
    :
elif PYTHON=$(command -v python3 2>/dev/null); then
    :
elif PYTHON=$(command -v python 2>/dev/null); then
    :
else
    printf 'A supported Python interpreter was not found.\n' >&2
    exit 1
fi

if ! "$PYTHON" "$SCRIPT_DIR/scripts/check_python_version.py" "$SCRIPT_DIR/pyproject.toml"; then
    exit 1
fi

if [[ "${1:-}" == "install" ]]; then
    if [[ "$#" -ne 1 ]]; then
        printf 'Usage: %s install\n' "$0" >&2
        exit 2
    fi

    if ! "$PYTHON" -m pip --version >/dev/null 2>&1; then
        printf 'pip is missing from %s; bootstrapping it with ensurepip...\n' "$PYTHON"
        if ! "$PYTHON" -m ensurepip --upgrade; then
            printf 'Unable to find or bootstrap pip for %s.\n' "$PYTHON" >&2
            exit 1
        fi
    fi

    printf 'Installing dependencies with %s...\n' "$PYTHON"
    exec "$PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt"
fi

export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" -m ethstaker_deposit "$@"
