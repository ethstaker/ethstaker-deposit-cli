import os
import time
import pytest
from ethstaker_deposit.credentials import Credential
from ethstaker_deposit.settings import get_chain_setting
from ethstaker_deposit.utils.constants import DEFAULT_BLS_TO_EXECUTION_CHANGES_KEYSTORE_FOLDER_NAME
from tests.shared_helpers import read_json_file, verify_file_permission
from tests.test_integration.helpers import run_deposit_cli


@pytest.mark.asyncio
async def test_script(deposit_cli_installed, cli_output_folder) -> None:
    # Generate a BLS-to-execution-change through deposit.sh from a keystore file.
    my_folder_path = cli_output_folder
    changes_folder_path = os.path.join(my_folder_path, DEFAULT_BLS_TO_EXECUTION_CHANGES_KEYSTORE_FOLDER_NAME)
    os.mkdir(changes_folder_path)

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

    keystore_filepath = credential.save_signing_keystore(keystore_password, changes_folder_path, time.time())

    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'generate-bls-to-execution-change-keystore',
        '--output_folder', my_folder_path,
        '--chain', chain,
        '--keystore', keystore_filepath,
        '--keystore_password', keystore_password,
        '--validator_index', '1',
        '--withdrawal_address', '0xcd60A5f152724480c3a95E4Ff4dacEEf4074854d',
    )

    _, _, files = next(os.walk(changes_folder_path))

    change_files = [f for f in files if 'bls_to_execution_change_keystore_' in f]

    assert len(set(change_files)) == 1

    json_data = read_json_file(changes_folder_path, change_files[0])

    assert json_data['message']['to_execution_address'] == '0xcd60a5f152724480c3a95e4ff4daceef4074854d'
    assert json_data['message']['validator_index'] == 1
    assert json_data['signature']

    verify_file_permission(os, folder_path=changes_folder_path, files=change_files)
