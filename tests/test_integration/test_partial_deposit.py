import json
import os
import pytest
import time
from eth_utils import to_normalized_address, decode_hex
from ethstaker_deposit.credentials import Credential
from ethstaker_deposit.settings import get_chain_setting
from ethstaker_deposit.utils.constants import (
    COMPOUNDING_WITHDRAWAL_PREFIX,
    DEFAULT_ACTIVATION_AMOUNT,
    DEFAULT_PARTIAL_DEPOSIT_FOLDER_NAME,
    ETH2GWEI,
)
from tests.shared_helpers import get_permissions
from tests.test_integration.helpers import run_deposit_cli


@pytest.mark.asyncio
async def test_script(deposit_cli_installed, cli_output_folder) -> None:
    # Generate a partial deposit through deposit.sh from a keystore file.
    my_folder_path = cli_output_folder
    partial_deposit_folder = os.path.join(my_folder_path, DEFAULT_PARTIAL_DEPOSIT_FOLDER_NAME)
    os.mkdir(partial_deposit_folder)

    chain_settings = get_chain_setting()
    password = "MyPasswordIs"
    withdrawal_address = "0xcd60A5f152724480c3a95E4Ff4dacEEf4074854d"
    mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    credential = Credential(
        mnemonic=mnemonic,
        mnemonic_password="",
        index=0,
        amount=32000000000,
        chain_setting=chain_settings,
        hex_withdrawal_address=to_normalized_address(withdrawal_address),
        compounding=False,
    )

    keystore_file_folder = credential.save_signing_keystore(password, partial_deposit_folder, time.time())

    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'partial-deposit',
        '--chain', 'mainnet',
        '--keystore', keystore_file_folder,
        '--keystore_password', password,
        '--amount', '32',
        '--withdrawal_address', withdrawal_address,
        '--output_folder', my_folder_path,
    )

    _, _, folder_files = next(os.walk(partial_deposit_folder))

    deposit_files = [deposit_file for deposit_file in folder_files if deposit_file.startswith('deposit')]

    assert len(deposit_files) == 1

    deposit_file = deposit_files[0]
    with open(partial_deposit_folder + '/' + deposit_file, encoding='utf-8') as f:
        deposits_dict = json.load(f)
    for deposit in deposits_dict:
        withdrawal_credentials = bytes.fromhex(deposit['withdrawal_credentials'])
        assert withdrawal_credentials == (
            COMPOUNDING_WITHDRAWAL_PREFIX + b'\x00' * 11 + decode_hex(withdrawal_address)
        )
        assert deposit['amount'] == DEFAULT_ACTIVATION_AMOUNT * ETH2GWEI

    if os.name == 'posix':
        assert get_permissions(partial_deposit_folder, deposit_files[0]) == '0o400'
