import os
import pytest
from ethstaker_deposit.settings import MainnetSetting
from ethstaker_deposit.utils.constants import DEFAULT_BLS_TO_EXECUTION_CHANGES_FOLDER_NAME
from tests.shared_helpers import (
    TEST_MNEMONIC,
    assert_btec_content,
    assert_btec_round_trip,
    verify_file_permission,
)
from tests.test_integration.helpers import run_deposit_cli, run_deposit_cli_capture


@pytest.mark.asyncio
async def test_script(deposit_cli_installed, cli_output_folder) -> None:
    # Generate a BLS-to-execution-change through deposit.sh from a mnemonic.
    my_folder_path = cli_output_folder

    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'generate-bls-to-execution-change',
        '--bls_to_execution_changes_folder', my_folder_path,
        '--chain', 'mainnet',
        '--mnemonic', TEST_MNEMONIC,
        '--bls_withdrawal_credentials_list', '0x00bd0b5a34de5fb17df08410b5e615dda87caf4fb72d0aac91ce5e52fc6aa8de',
        '--validator_start_index', '0',
        '--validator_indices', '1',
        '--withdrawal_address', '0x3434343434343434343434343434343434343434',
    )

    # Check files
    bls_to_execution_changes_folder_path = os.path.join(my_folder_path, DEFAULT_BLS_TO_EXECUTION_CHANGES_FOLDER_NAME)
    _, _, btec_files = next(os.walk(bls_to_execution_changes_folder_path))

    btec_file = assert_btec_content(bls_to_execution_changes_folder_path, [1])
    assert_btec_round_trip(
        btec_file,
        mnemonic=TEST_MNEMONIC,
        start_index=0,
        validator_indices=[1],
        withdrawal_address='0x3434343434343434343434343434343434343434',
        chain_setting=MainnetSetting,
    )

    # Verify file permissions
    verify_file_permission(os, folder_path=bls_to_execution_changes_folder_path, files=btec_files)


def test_script_mismatched_credentials(deposit_cli_installed, cli_output_folder) -> None:
    '''
    When the supplied BLS withdrawal credentials do not match the mnemonic, the
    CLI reports the mismatch but currently exits 0 and writes no change file
    (see generate_bls_to_execution_change.py, which echoes `[Error]` and returns
    without raising). This documents the current process-level behavior.
    '''
    my_folder_path = cli_output_folder

    result = run_deposit_cli_capture(
        '--language', 'english',
        '--non_interactive',
        'generate-bls-to-execution-change',
        '--bls_to_execution_changes_folder', my_folder_path,
        '--chain', 'mainnet',
        '--mnemonic', TEST_MNEMONIC,
        '--bls_withdrawal_credentials_list', '0x0011111111111111111111111111111111111111111111111111111111111111',
        '--validator_start_index', '0',
        '--validator_indices', '1',
        '--withdrawal_address', '0x3434343434343434343434343434343434343434',
    )

    assert result.returncode == 0
    assert b'[Error]' in result.stdout

    bls_to_execution_changes_folder_path = os.path.join(my_folder_path, DEFAULT_BLS_TO_EXECUTION_CHANGES_FOLDER_NAME)
    assert os.path.exists(bls_to_execution_changes_folder_path)
    assert os.listdir(bls_to_execution_changes_folder_path) == []
