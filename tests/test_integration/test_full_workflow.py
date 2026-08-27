import json
import os

import pytest

from ethstaker_deposit.settings import MainnetSetting
from ethstaker_deposit.utils.constants import (
    DEFAULT_ACTIVATION_AMOUNT,
    DEFAULT_BLS_TO_EXECUTION_CHANGES_KEYSTORE_FOLDER_NAME,
    DEFAULT_EXIT_TRANSACTION_FOLDER_NAME,
    DEFAULT_PARTIAL_DEPOSIT_FOLDER_NAME,
    DEFAULT_VALIDATOR_KEYS_FOLDER_NAME,
    ETH2GWEI,
)
from ethstaker_deposit.utils.validation import verify_bls_to_execution_change_keystore_json
from tests.shared_helpers import read_json_file
from tests.test_integration.helpers import run_deposit_cli

MNEMONIC = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
KEYSTORE_PASSWORD = 'MyPasswordIs'
WITHDRAWAL_ADDRESS = '0x00000000219ab540356cBB839Cbe05303d7705Fa'


@pytest.mark.asyncio
async def test_keygen_to_consumers(deposit_cli_installed, cli_output_folder) -> None:
    '''
    The full product workflow: generate keystores through deposit.sh, then feed
    the on-disk keystores into the keystore-consuming commands in separate
    processes.
    '''
    my_folder_path = cli_output_folder

    # Part 1: generate keystores through deposit.sh.
    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'existing-mnemonic',
        '--num_validators', '1',
        '--mnemonic', MNEMONIC,
        '--validator_start_index', '0',
        '--chain', 'mainnet',
        '--keystore_password', KEYSTORE_PASSWORD,
        '--withdrawal_address', WITHDRAWAL_ADDRESS,
        '--folder', my_folder_path,
    )

    keys_folder = os.path.join(my_folder_path, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    keystore_file = [f for f in os.listdir(keys_folder) if f.startswith('keystore')][0]
    keystore_path = os.path.join(keys_folder, keystore_file)
    keystore_data = read_json_file(keys_folder, keystore_file)
    pubkey = keystore_data['pubkey']

    # Part 2: sign an exit transaction with the on-disk keystore.
    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'exit-transaction-keystore',
        '--output_folder', my_folder_path,
        '--chain', 'mainnet',
        '--keystore', keystore_path,
        '--keystore_password', KEYSTORE_PASSWORD,
        '--validator_index', '0',
        '--epoch', '1234',
    )

    exit_folder = os.path.join(my_folder_path, DEFAULT_EXIT_TRANSACTION_FOLDER_NAME)
    exit_file = [f for f in os.listdir(exit_folder) if 'signed_exit' in f][0]
    exit_data = read_json_file(exit_folder, exit_file)
    assert exit_data['message']['validator_index'] == '0'
    assert exit_data['message']['epoch'] == '1234'
    assert exit_data['signature']

    # Part 3: sign a BLS-to-execution-change with the on-disk keystore.
    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'generate-bls-to-execution-change-keystore',
        '--output_folder', my_folder_path,
        '--chain', 'mainnet',
        '--keystore', keystore_path,
        '--keystore_password', KEYSTORE_PASSWORD,
        '--validator_index', '0',
        '--withdrawal_address', WITHDRAWAL_ADDRESS,
    )

    btec_folder = os.path.join(my_folder_path, DEFAULT_BLS_TO_EXECUTION_CHANGES_KEYSTORE_FOLDER_NAME)
    btec_file = [f for f in os.listdir(btec_folder) if 'bls_to_execution_change_keystore_' in f][0]
    btec_path = os.path.join(btec_folder, btec_file)
    btec_data = read_json_file(btec_folder, btec_file)
    assert btec_data['message']['validator_index'] == 0
    assert btec_data['message']['to_execution_address'] == WITHDRAWAL_ADDRESS.lower()
    assert btec_data['signature']
    # The change must verify against the keystore's pubkey.
    assert verify_bls_to_execution_change_keystore_json(btec_path, pubkey, MainnetSetting)

    # Part 4: verify the keystore password through deposit.sh.
    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'test-keystore',
        '--keystore', keystore_path,
        '--keystore_password', KEYSTORE_PASSWORD,
    )

    # Part 5: generate a partial deposit with the on-disk keystore.
    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'partial-deposit',
        '--chain', 'mainnet',
        '--keystore', keystore_path,
        '--keystore_password', KEYSTORE_PASSWORD,
        '--amount', '32',
        '--withdrawal_address', WITHDRAWAL_ADDRESS,
        '--output_folder', my_folder_path,
    )

    partial_deposit_folder = os.path.join(my_folder_path, DEFAULT_PARTIAL_DEPOSIT_FOLDER_NAME)
    deposit_file = [f for f in os.listdir(partial_deposit_folder) if f.startswith('deposit')][0]
    with open(os.path.join(partial_deposit_folder, deposit_file), encoding='utf-8') as f:
        deposits_dict = json.load(f)
    assert len(deposits_dict) == 1
    deposit = deposits_dict[0]
    assert deposit['pubkey'] == pubkey
    assert deposit['amount'] == DEFAULT_ACTIVATION_AMOUNT * ETH2GWEI
