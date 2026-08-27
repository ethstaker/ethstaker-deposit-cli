import os
import time
import pytest
from ethstaker_deposit.credentials import Credential
from ethstaker_deposit.settings import get_chain_setting
from ethstaker_deposit.utils.constants import DEFAULT_VALIDATOR_KEYS_FOLDER_NAME
from ethstaker_deposit.utils.intl import load_text
from tests.test_integration.helpers import run_deposit_cli, run_deposit_cli_capture


@pytest.mark.asyncio
async def test_script(deposit_cli_installed, cli_output_folder) -> None:
    # Verify a keystore password through deposit.sh.
    my_folder_path = cli_output_folder
    keys_folder_path = os.path.join(my_folder_path, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    os.mkdir(keys_folder_path)

    keystore_password = 'solo-stakers'

    credential = Credential(
        mnemonic='aban aban aban aban aban aban aban aban aban aban aban abou',
        mnemonic_password='',
        index=0,
        amount=0,
        chain_setting=get_chain_setting('mainnet'),
        hex_withdrawal_address=None,
        compounding=False,
    )

    keystore_filepath = credential.save_signing_keystore(keystore_password, keys_folder_path, time.time())

    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'test-keystore',
        '--keystore', keystore_filepath,
        '--keystore_password', keystore_password,
    )


def test_script_wrong_password(deposit_cli_installed, cli_output_folder) -> None:
    # A wrong keystore password must exit non-zero with the mismatch message on stderr.
    my_folder_path = cli_output_folder
    keys_folder_path = os.path.join(my_folder_path, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    os.mkdir(keys_folder_path)

    keystore_password = 'solo-stakers'

    credential = Credential(
        mnemonic='aban aban aban aban aban aban aban aban aban aban aban abou',
        mnemonic_password='',
        index=0,
        amount=0,
        chain_setting=get_chain_setting('mainnet'),
        hex_withdrawal_address=None,
        compounding=False,
    )

    keystore_filepath = credential.save_signing_keystore(keystore_password, keys_folder_path, time.time())

    result = run_deposit_cli_capture(
        '--language', 'english',
        '--non_interactive',
        'test-keystore',
        '--keystore', keystore_filepath,
        '--keystore_password', 'very_wrong_password',
    )

    assert result.returncode == 1
    mismatch_msg = load_text(
        ['arg_test_keystore_keystore_password', 'mismatch'],
        os.path.join(os.getcwd(), 'ethstaker_deposit/cli/', 'test_keystore.json'),
        'test_keystore',
        'en',
    )
    assert mismatch_msg.encode() in result.stderr
