import os
import pytest
from ethstaker_deposit.utils.constants import DEFAULT_EXIT_TRANSACTION_FOLDER_NAME
from tests.shared_helpers import read_json_file, verify_file_permission
from tests.test_integration.helpers import run_deposit_cli


@pytest.mark.asyncio
async def test_exit_transaction_mnemonic_multiple(deposit_cli_installed, cli_output_folder) -> None:
    my_folder_path = cli_output_folder

    cmd_args = [
        '--language', 'english',
        '--non_interactive',
        'exit-transaction-mnemonic',
        '--output_folder', my_folder_path,
        '--chain', 'mainnet',
        '--mnemonic', 'aban aban aban aban aban aban aban aban aban aban aban abou',
        '--validator_start_index', '0',
        '--validator_indices', '0,1,2,3',
        '--epoch', '1234',
    ]
    await run_deposit_cli(*cmd_args)

    # Check files
    exit_transaction_folder_path = os.path.join(my_folder_path, DEFAULT_EXIT_TRANSACTION_FOLDER_NAME)
    _, _, exit_transaction_files = next(os.walk(exit_transaction_folder_path))

    assert len(set(exit_transaction_files)) == 4

    # Verify file content
    exit_transaction_files.sort()
    for index in [0, 1, 2, 3]:
        json_data = read_json_file(exit_transaction_folder_path, exit_transaction_files[index])
        assert json_data['message']['epoch'] == '1234'
        assert json_data['message']['validator_index'] == str(index)
        assert json_data['signature']

    # Verify file permissions
    verify_file_permission(os, folder_path=exit_transaction_folder_path, files=exit_transaction_files)
