import os

import pytest

from eth_utils import decode_hex

from ethstaker_deposit.credentials import Credential
from ethstaker_deposit.settings import DEPOSIT_CLI_VERSION, get_chain_setting
from ethstaker_deposit.utils.constants import (
    BUILDER_WITHDRAWAL_PREFIX,
    DEFAULT_BUILDER_KEYS_FOLDER_NAME,
    ETH2GWEI,
)
from ethstaker_deposit.utils.validation import verify_builder_deposit_data_json
from tests.shared_helpers import get_permissions, read_json_file
from tests.test_integration.helpers import run_deposit_cli, run_deposit_cli_capture

MNEMONIC = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
WITHDRAWAL_ADDRESS = '0x00000000219ab540356cBB839Cbe05303d7705Fa'
KEYSTORE_PASSWORD = 'MyPasswordIs'


@pytest.mark.asyncio
async def test_script(deposit_cli_installed, cli_output_folder) -> None:
    # Generate builder keys through deposit.sh from an existing mnemonic.
    my_folder_path = cli_output_folder

    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'builder',
        '--mnemonic', MNEMONIC,
        '--builder_start_index', '0',
        '--num_builders', '2',
        '--chain', 'mainnet',
        '--keystore_password', KEYSTORE_PASSWORD,
        '--withdrawal_address', WITHDRAWAL_ADDRESS,
        '--builder_amount', '1',
        '--folder', my_folder_path,
    )

    builder_keys_folder = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    _, _, files = next(os.walk(builder_keys_folder))

    keystore_files = [f for f in files if f.startswith('keystore')]
    deposit_files = [f for f in files if f.startswith('builder_deposit_data')]
    assert len(keystore_files) == 2
    assert len(deposit_files) == 1

    deposits = read_json_file(builder_keys_folder, deposit_files[0])
    assert len(deposits) == 2

    keystore_pubkeys = {
        read_json_file(builder_keys_folder, key_file)['pubkey'] for key_file in keystore_files
    }
    for deposit in deposits:
        assert bytes.fromhex(deposit['withdrawal_credentials']) == (
            BUILDER_WITHDRAWAL_PREFIX + b'\x00' * 11 + decode_hex(WITHDRAWAL_ADDRESS)
        )
        assert deposit['amount'] == ETH2GWEI
        assert deposit['pubkey'] in keystore_pubkeys
        assert deposit['network_name'] == 'mainnet'
        assert deposit['deposit_cli_version'] == DEPOSIT_CLI_VERSION
        assert deposit['signature']

    # Each builder deposit must verify against an independently derived credential,
    # exercising the in-process signature/root validation of the real product.
    credentials = [
        Credential(
            mnemonic=MNEMONIC,
            mnemonic_password='',
            index=index,
            amount=ETH2GWEI,
            chain_setting=get_chain_setting('mainnet'),
            hex_withdrawal_address=WITHDRAWAL_ADDRESS,
            is_builder=True,
        )
        for index in range(2)
    ]
    assert verify_builder_deposit_data_json(os.path.join(builder_keys_folder, deposit_files[0]), credentials)

    # Verify file permissions
    if os.name == 'posix':
        for file_name in files:
            assert get_permissions(builder_keys_folder, file_name) == '0o400'


def test_script_builder_amount_below_minimum(deposit_cli_installed, cli_output_folder) -> None:
    # Builder deposits have a 1 ETH minimum; a smaller amount must exit non-zero
    # and create no artifacts.
    my_folder_path = cli_output_folder

    result = run_deposit_cli_capture(
        '--language', 'english',
        '--non_interactive',
        'builder',
        '--mnemonic', MNEMONIC,
        '--builder_start_index', '0',
        '--num_builders', '1',
        '--chain', 'mainnet',
        '--keystore_password', KEYSTORE_PASSWORD,
        '--withdrawal_address', WITHDRAWAL_ADDRESS,
        '--builder_amount', '0.5',
        '--folder', my_folder_path,
    )

    assert result.returncode == 1
    assert b'Error' in result.stderr
    assert not os.path.exists(os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME))


def test_script_missing_withdrawal_address(deposit_cli_installed, cli_output_folder) -> None:
    # Builders have no BLS-only withdrawal type, so an execution withdrawal
    # address is always required.
    my_folder_path = cli_output_folder

    result = run_deposit_cli_capture(
        '--language', 'english',
        '--non_interactive',
        'builder',
        '--mnemonic', MNEMONIC,
        '--builder_start_index', '0',
        '--num_builders', '1',
        '--chain', 'mainnet',
        '--keystore_password', KEYSTORE_PASSWORD,
        '--builder_amount', '1',
        '--folder', my_folder_path,
    )

    assert result.returncode == 1
    assert b'Error' in result.stderr
    assert not os.path.exists(os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME))
