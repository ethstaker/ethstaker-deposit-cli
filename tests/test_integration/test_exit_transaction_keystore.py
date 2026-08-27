import os
import time
import pytest
from ethstaker_deposit.credentials import Credential
from ethstaker_deposit.settings import get_chain_setting
from ethstaker_deposit.utils.constants import DEFAULT_EXIT_TRANSACTION_FOLDER_NAME
from ethstaker_deposit.utils.intl import (
    load_text,
)
from tests.shared_helpers import read_json_file, verify_file_permission
from tests.test_integration.helpers import run_deposit_cli, run_deposit_cli_capture


@pytest.mark.asyncio
async def test_script(deposit_cli_installed, cli_output_folder) -> None:
    # Generate an exit transaction through deposit.sh from a keystore file.
    my_folder_path = cli_output_folder
    exit_transaction_folder_path = os.path.join(my_folder_path, DEFAULT_EXIT_TRANSACTION_FOLDER_NAME)
    os.mkdir(exit_transaction_folder_path)

    chain = 'mainnet'
    keystore_password = 'solo-stakers'

    credential = Credential(
        mnemonic='aban aban aban aban aban aban aban aban aban aban aban abou',
        mnemonic_password='',
        index=0,
        amount=0,
        chain_setting=get_chain_setting(chain),
        hex_withdrawal_address=None,
        compounding=False,
    )

    keystore_filepath = credential.save_signing_keystore(keystore_password, exit_transaction_folder_path, time.time())

    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'exit-transaction-keystore',
        '--output_folder', my_folder_path,
        '--chain', chain,
        '--keystore', keystore_filepath,
        '--keystore_password', keystore_password,
        '--validator_index', '1',
        '--epoch', '1234',
    )

    # Check files
    _, _, exit_transaction_files = next(os.walk(exit_transaction_folder_path))

    # Filter files to signed_exit as keystore file will exist as well
    exit_transaction_file = [f for f in exit_transaction_files if 'signed_exit' in f]

    assert len(set(exit_transaction_file)) == 1

    json_data = read_json_file(exit_transaction_folder_path, exit_transaction_file[0])

    # Verify file content
    assert json_data['message']['epoch'] == '1234'
    assert json_data['message']['validator_index'] == '1'
    assert json_data['signature']

    # Verify file permissions
    verify_file_permission(os, folder_path=exit_transaction_folder_path, files=exit_transaction_file)


def test_script_wrong_password(deposit_cli_installed, cli_output_folder) -> None:
    # A wrong keystore password must exit non-zero, report on stderr and write no file.
    my_folder_path = cli_output_folder
    exit_transaction_folder_path = os.path.join(my_folder_path, DEFAULT_EXIT_TRANSACTION_FOLDER_NAME)
    os.mkdir(exit_transaction_folder_path)

    chain = 'mainnet'
    keystore_password = 'solo-stakers'

    credential = Credential(
        mnemonic='aban aban aban aban aban aban aban aban aban aban aban abou',
        mnemonic_password='',
        index=0,
        amount=0,
        chain_setting=get_chain_setting(chain),
        hex_withdrawal_address=None,
        compounding=False,
    )

    keystore_filepath = credential.save_signing_keystore(keystore_password, exit_transaction_folder_path, time.time())

    result = run_deposit_cli_capture(
        '--language', 'english',
        '--non_interactive',
        'exit-transaction-keystore',
        '--output_folder', my_folder_path,
        '--chain', chain,
        '--keystore', keystore_filepath,
        '--keystore_password', 'very_wrong_password',
        '--validator_index', '1',
        '--epoch', '1234',
    )

    assert result.returncode == 1
    mismatch_msg = load_text(
        ['arg_exit_transaction_keystore_keystore_password', 'mismatch'],
        os.path.join(os.getcwd(), 'ethstaker_deposit/cli/', 'exit_transaction_keystore.json'),
        'exit_transaction_keystore',
        'en',
    )
    assert mismatch_msg.encode() in result.stderr

    _, _, files = next(os.walk(exit_transaction_folder_path))
    assert not [f for f in files if 'signed_exit' in f]
