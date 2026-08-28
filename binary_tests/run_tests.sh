#!/usr/bin/env bash
#
# binary_tests/run_tests.sh - interactive release-asset tests for the compiled
# ethstaker-deposit-cli binary.
#
# These tests replace the legacy root-level test_binary_*.py scripts. They drive
# the compiled `deposit` binary over a PTY with expect, exercising the fully
# interactive happy path of every CLI command (prompts, "press any key" pauses,
# screen clears, mnemonic retype) and then assert the produced output files.
# They are intended to run across all supported target architectures on
# Linux/macOS, where expect is available; Windows release assets remain covered
# by the `--version` smoke test in .github/workflows/build.yml.
#
# Usage:
#   ./binary_tests/run_tests.sh <binary-dir>           run the full suite
#   ./binary_tests/run_tests.sh -s <name> <binary-dir>  run a single test
#   ./binary_tests/run_tests.sh -l                      list the available tests
#
# <binary-dir> must contain the compiled binary (`deposit` or `deposit.exe`),
# e.g. `./dist` after `make build_linux` / `make build_macos`, or an unpacked
# CI archive folder.
#
# Requires `expect` on PATH (apt install expect / brew install expect).

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

KEYSTORE_PASSWORD='MyPasswordIs'
WITHDRAWAL_ADDRESS='0x00000000219ab540356cBB839Cbe05303d7705Fa'
BTEC_WITHDRAWAL_ADDRESS='0x3434343434343434343434343434343434343434'
MNEMONIC='abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
BTEC_MNEMONIC='sister protect peanut hill ready work profit fit wish want small inflict flip member tail between sick setup bright duck morning sell paper worry'
BTEC_CREDENTIALS='0x00bd0b5a34de5fb17df08410b5e615dda87caf4fb72d0aac91ce5e52fc6aa8de'
BTEC_VALIDATOR_INDEX='1'

ALL_TESTS=(
    tty
    new_mnemonic
    existing_mnemonic
    generate_mnemonic
    generate_bls_to_execution_change
    generate_bls_to_execution_change_keystore
    exit_transaction_keystore
    exit_transaction_mnemonic
    partial_deposit
    test_keystore
    builder
)

usage() {
    sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
}

fail_test() {
    echo "    FAIL: $*"
    return 1
}

count_files() {
    local dir="$1" glob="$2"
    if [[ ! -d "$dir" ]]; then
        echo 0
        return
    fi
    find "$dir" -maxdepth 1 -name "$glob" | wc -l
}

assert_keys() {
    local dir="$1" num="$2"
    local ks_count dep_count
    ks_count=$(count_files "$dir" 'keystore-*.json')
    dep_count=$(count_files "$dir" 'deposit_data-*.json')
    [[ "$ks_count" -eq "$num" ]] || fail_test "expected $num keystore-*.json in $dir, found $ks_count"
    [[ "$dep_count" -eq "$num" ]] || fail_test "expected $num deposit_data-*.json in $dir, found $dep_count"
    if [[ "$(uname -s)" != MINGW* ]]; then
        local ks mode
        for ks in "$dir"/keystore-*.json; do
            [[ -f "$ks" ]] || continue
            mode=$(stat -c '%a' "$ks" 2>/dev/null || stat -f '%Lp' "$ks" 2>/dev/null)
            [[ "$mode" == "400" ]] || fail_test "keystore $ks has mode $mode (expected 400)"
        done
    fi
}

assert_new_mnemonic() {
    assert_keys "$WORK_ROOT/out_new_mnemonic/validator_keys" 1
}

assert_existing_mnemonic() {
    assert_keys "$WORK_ROOT/out_existing_mnemonic/validator_keys" 1
}

assert_generate_mnemonic() {
    [[ -s "$WORK_ROOT/out_generate_mnemonic/mnemonic.txt" ]] || fail_test "mnemonic.txt missing or empty"
}

assert_btec() {
    local dir="$WORK_ROOT/out_generate_bls_to_execution_change/bls_to_execution_changes"
    local count
    count=$(count_files "$dir" 'bls_to_execution_change-*.json')
    [[ "$count" -ge 1 ]] || fail_test "no bls_to_execution_change JSON files in $dir"
}

assert_btec_keystore() {
    local dir="$WORK_ROOT/out_generate_bls_to_execution_change_keystore/bls_to_execution_changes_keystore"
    local count
    count=$(count_files "$dir" 'bls_to_execution_change_keystore_signature-*.json')
    [[ "$count" -ge 1 ]] || fail_test "no bls_to_execution_change_keystore_signature JSON files in $dir"
}

assert_exit_keystore() {
    local dir="$WORK_ROOT/out_exit_transaction_keystore/exit_transactions"
    local count
    count=$(count_files "$dir" 'signed_exit_transaction-*.json')
    [[ "$count" -ge 1 ]] || fail_test "no signed_exit_transaction JSON files in $dir"
}

assert_exit_mnemonic() {
    local dir="$WORK_ROOT/out_exit_transaction_mnemonic/exit_transactions"
    local count
    count=$(count_files "$dir" 'signed_exit_transaction-*.json')
    [[ "$count" -eq 4 ]] || fail_test "expected 4 signed_exit_transaction JSON files in $dir, found $count"
}

assert_partial_deposit() {
    local dir="$WORK_ROOT/out_partial_deposit/partial_deposits"
    local count
    count=$(count_files "$dir" 'deposit_data-*.json')
    [[ "$count" -ge 1 ]] || fail_test "no deposit_data JSON files in $dir"
}

assert_builder() {
    local dir="$WORK_ROOT/out_builder/builder_keys"
    local ks_count bd_count
    ks_count=$(count_files "$dir" 'keystore-*.json')
    bd_count=$(count_files "$dir" 'builder_deposit_data-*.json')
    [[ "$ks_count" -eq 1 ]] || fail_test "expected 1 keystore-*.json in $dir, found $ks_count"
    [[ "$bd_count" -eq 1 ]] || fail_test "expected 1 builder_deposit_data-*.json in $dir, found $bd_count"
}

assert_func() {
    case "$1" in
        tty) return 0 ;;
        new_mnemonic) assert_new_mnemonic ;;
        existing_mnemonic) assert_existing_mnemonic ;;
        generate_mnemonic) assert_generate_mnemonic ;;
        generate_bls_to_execution_change) assert_btec ;;
        generate_bls_to_execution_change_keystore) assert_btec_keystore ;;
        exit_transaction_keystore) assert_exit_keystore ;;
        exit_transaction_mnemonic) assert_exit_mnemonic ;;
        partial_deposit) assert_partial_deposit ;;
        test_keystore) return 0 ;;
        builder) assert_builder ;;
        *) return 1 ;;
    esac
}

needs_keystore() {
    case "$1" in
        generate_bls_to_execution_change_keystore | exit_transaction_keystore | partial_deposit | test_keystore)
            return 0 ;;
        *) return 1 ;;
    esac
}

PASS_COUNT=0
FAIL_COUNT=0
FAILED_TESTS=()

run_test() {
    local name="$1"
    local work="$WORK_ROOT/out_$name"
    local log="$WORK_ROOT/log_$name.txt"
    local expect_script="$SCRIPT_DIR/test_$name.exp"

    mkdir -p "$work"

    # Keystore-consuming tests need the fixture keystore produced by
    # existing_mnemonic; run it as a prerequisite when it has not run yet.
    if needs_keystore "$name" && [[ -z "${KEYSTORE_PATH:-}" ]]; then
        echo "==> Prerequisite: existing_mnemonic (creates the keystore fixture)"
        run_test existing_mnemonic || true
        if [[ -z "${KEYSTORE_PATH:-}" ]]; then
            echo "    FAIL (keystore fixture unavailable)"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            FAILED_TESTS+=("$name")
            return 1
        fi
    fi

    echo "==> Running test: $name"
    # The prerequisite run changed WORK_DIR; point it back at this test's folder.
    export WORK_DIR="$work"
    if (cd "$WORK_ROOT" && expect "$expect_script") >"$log" 2>&1; then
        if assert_func "$name"; then
            echo "    PASS"
            PASS_COUNT=$((PASS_COUNT + 1))
            if [[ "$name" == "existing_mnemonic" ]]; then
                local keystore_glob
                keystore_glob=( "$work/validator_keys"/keystore-*.json )
                if [[ -f "${keystore_glob[0]}" ]]; then
                    KEYSTORE_PATH="${keystore_glob[0]}"
                    export KEYSTORE_PATH
                fi
            fi
        else
            echo "    FAIL (output files)"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            FAILED_TESTS+=("$name")
        fi
    else
        echo "    FAIL (interactive run)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILED_TESTS+=("$name")
        tail -n 60 "$log" | sed 's/^/    | /'
    fi
}

SELECTED=""
LIST_ONLY=0
BINARY_DIR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -s | --select)
            [[ $# -ge 2 ]] || { echo "Error: -s requires a test name." >&2; exit 2; }
            SELECTED="$2"
            shift 2
            ;;
        -l | --list)
            LIST_ONLY=1
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage
            exit 2
            ;;
        *)
            [[ -z "$BINARY_DIR" ]] || { echo "Error: unexpected extra argument: $1" >&2; exit 2; }
            BINARY_DIR="$1"
            shift
            ;;
    esac
done

if [[ "$LIST_ONLY" == 1 ]]; then
    echo "Available tests:"
    printf '  %s\n' "${ALL_TESTS[@]}"
    exit 0
fi

if [[ -z "$BINARY_DIR" ]]; then
    echo "Error: missing <binary-dir> argument." >&2
    usage
    exit 2
fi

if ! command -v expect >/dev/null 2>&1; then
    echo "Error: 'expect' is required but not found on PATH." >&2
    echo "  Debian/Ubuntu: sudo apt-get install expect" >&2
    echo "  macOS:         brew install expect" >&2
    exit 2
fi

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

# Resolve to an absolute path: the expect scripts run from the temporary work dir.
BINARY="$(cd -- "$(dirname -- "$BINARY")" && pwd)/$(basename -- "$BINARY")"

if [[ -n "$SELECTED" ]]; then
    case " ${ALL_TESTS[*]} " in
        *" $SELECTED "*) TESTS=("$SELECTED") ;;
        *) echo "Error: unknown test '$SELECTED'. Use -l to list tests." >&2; exit 2 ;;
    esac
else
    TESTS=("${ALL_TESTS[@]}")
fi

export BINARY
export KEYSTORE_PASSWORD WITHDRAWAL_ADDRESS BTEC_WITHDRAWAL_ADDRESS
export MNEMONIC BTEC_MNEMONIC BTEC_CREDENTIALS BTEC_VALIDATOR_INDEX
export VERSION_FILE="$REPO_ROOT/ethstaker_deposit/VERSION"
export TERM="${TERM:-xterm}"

WORK_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/binary_tests.XXXXXX")"
WORK_ROOT="$(cd "$WORK_ROOT" && pwd -P)"
trap 'rm -rf "$WORK_ROOT"' EXIT

echo "Testing binary: $BINARY"
echo "Python used to build the binary (target): 3.14"
echo "Working directory: $WORK_ROOT"
echo

for t in "${TESTS[@]}"; do
    run_test "$t"
done

echo
echo "===== binary test results: $PASS_COUNT passed, $FAIL_COUNT failed ====="
if ((FAIL_COUNT > 0)); then
    printf 'Failed tests: %s\n' "${FAILED_TESTS[@]}"
    exit 1
fi
exit 0
