#!/usr/bin/env bash
#
# binary_tests/test_non_interactive.sh - non-interactive release-asset test for
# the compiled ethstaker-deposit-cli binary.
#
# Unlike the other binary_tests (which drive the interactive happy path over a
# PTY with expect), this test covers the --non_interactive flow that needs no
# terminal at all: the mnemonic is written straight to --output_file and the
# process exits silently. It only checks the exit code and the produced file,
# so it needs no expect and runs on Windows too (via Git Bash).
#
# Usage:
#   ./binary_tests/test_non_interactive.sh <binary-dir>
#
# <binary-dir> must contain the compiled binary (`deposit` or `deposit.exe`).

set -euo pipefail

usage() {
    sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
}

if [[ $# -ne 1 ]]; then
    echo "Error: missing <binary-dir> argument." >&2
    usage
    exit 2
fi

BINARY_DIR="$1"

if [[ -f "$BINARY_DIR/deposit" ]]; then
    BINARY="$BINARY_DIR/deposit"
elif [[ -f "$BINARY_DIR/deposit.exe" ]]; then
    BINARY="$BINARY_DIR/deposit.exe"
else
    echo "Error: no 'deposit' or 'deposit.exe' found in '$BINARY_DIR'." >&2
    exit 2
fi

if [[ ! -x "$BINARY" ]]; then
    echo "Error: '$BINARY' is not executable." >&2
    exit 2
fi

BINARY="$(cd -- "$(dirname -- "$BINARY")" && pwd)/$(basename -- "$BINARY")"

WORK_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/binary_noninteractive.XXXXXX")"
trap 'rm -rf "$WORK_ROOT"' EXIT

export TERM="${TERM:-xterm}"

echo "Testing binary: $BINARY"
echo "Working directory: $WORK_ROOT"
echo

# cd into the temp work dir (which lives under /tmp) so the relative
# --output_file does not pass through a symlinked path on macOS.
cd "$WORK_ROOT"
OUTPUT_FILE=./test-mnemonic.txt
LOG="$WORK_ROOT/log.txt"

if "$BINARY" --non_interactive --ignore_connectivity --language english \
    generate-mnemonic --mnemonic_language english --output_file "$OUTPUT_FILE" >"$LOG" 2>&1; then
    echo "    exit code: 0"
else
    echo "    FAIL: non-interactive run exited non-zero" >&2
    tail -n 60 "$LOG" | sed 's/^/    | /' >&2
    exit 1
fi

if [[ ! -f "$OUTPUT_FILE" ]]; then
    echo "    FAIL: $OUTPUT_FILE was not created" >&2
    exit 1
fi

if [[ ! -s "$OUTPUT_FILE" ]]; then
    echo "    FAIL: $OUTPUT_FILE is empty" >&2
    exit 1
fi

word_count=$(wc -w <"$OUTPUT_FILE")
if [[ "$word_count" -ne 24 ]]; then
    echo "    FAIL: $OUTPUT_FILE has $word_count words (expected 24)" >&2
    exit 1
fi

if [[ "$(uname -s)" != MINGW* ]]; then
    mode=$(stat -c '%a' "$OUTPUT_FILE" 2>/dev/null || stat -f '%Lp' "$OUTPUT_FILE" 2>/dev/null)
    if [[ "$mode" != "400" ]]; then
        echo "    FAIL: $OUTPUT_FILE has mode $mode (expected 400)" >&2
        exit 1
    fi
fi

echo "    PASS: mnemonic written to $OUTPUT_FILE (24 words)"
