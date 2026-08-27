import json
import os

import pytest
from click.testing import CliRunner

from eth_utils import decode_hex

from ethstaker_deposit.cli import builder
from ethstaker_deposit.deposit import cli
from ethstaker_deposit.utils.constants import (
    BUILDER_WITHDRAWAL_PREFIX,
    DEFAULT_BUILDER_KEYS_FOLDER_NAME,
    ETH2GWEI,
)
from .helpers import clean_builder_folder
from tests.shared_helpers import get_permissions, get_uuid


def test_builder_new_mnemonic(monkeypatch) -> None:
    # monkeypatch get_mnemonic
    def mock_get_mnemonic(language, words_path, entropy=None) -> str:
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    monkeypatch.setattr(builder, "get_mnemonic", mock_get_mnemonic)

    # Prepare folder
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    runner = CliRunner()
    withdrawal_address = '0x00000000219ab540356cBB839Cbe05303d7705Fa'
    inputs = [
        'english',  # top-level CLI language
        'no',  # no existing mnemonic -> generate a new one
        'english',  # mnemonic wordlist language
        '1',  # num_builders
        'mainnet',  # chain
        'MyPasswordIs', 'MyPasswordIs',  # keystore password + confirm
        withdrawal_address, withdrawal_address,  # withdrawal address + confirm
        '1',  # builder_amount
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
    ]
    data = '\n'.join(inputs)
    arguments = [
        '--ignore_connectivity',
        'builder',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments, input=data)
    assert result.exit_code == 0

    # Check files
    builder_keys_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(builder_keys_folder_path))

    deposit_file = [key_file for key_file in key_files if key_file.startswith('builder_deposit_data')][0]
    with open(builder_keys_folder_path + '/' + deposit_file, encoding='utf-8') as f:
        deposits_dict = json.load(f)
    assert len(deposits_dict) == 1
    for deposit in deposits_dict:
        withdrawal_credentials = bytes.fromhex(deposit['withdrawal_credentials'])
        assert withdrawal_credentials == (
            BUILDER_WITHDRAWAL_PREFIX + b'\x00' * 11 + decode_hex(withdrawal_address)
        )
        assert deposit['amount'] == ETH2GWEI

    all_uuid = [
        get_uuid(builder_keys_folder_path + '/' + key_file)
        for key_file in key_files
        if key_file.startswith('keystore')
    ]
    assert len(set(all_uuid)) == 1

    # Verify file permissions
    if os.name == 'posix':
        for file_name in key_files:
            assert get_permissions(builder_keys_folder_path, file_name) == '0o400'

    # Clean up
    clean_builder_folder(my_folder_path)


def test_builder_existing_mnemonic_via_confirm() -> None:
    # Prepare folder
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    runner = CliRunner()
    withdrawal_address = '0x00000000219ab540356cBB839Cbe05303d7705Fa'
    inputs = [
        'english',  # top-level CLI language
        'yes',  # has an existing mnemonic
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '0', '0',  # builder_start_index + confirm
        '2',  # num_builders
        'mainnet',  # chain
        'MyPasswordIs', 'MyPasswordIs',
        withdrawal_address, withdrawal_address,
        '1',  # builder_amount
    ]
    data = '\n'.join(inputs)
    arguments = [
        '--ignore_connectivity',
        'builder',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments, input=data)
    assert result.exit_code == 0

    builder_keys_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(builder_keys_folder_path))

    all_uuid = [
        get_uuid(builder_keys_folder_path + '/' + key_file)
        for key_file in key_files
        if key_file.startswith('keystore')
    ]
    assert len(set(all_uuid)) == 2

    if os.name == 'posix':
        for file_name in key_files:
            assert get_permissions(builder_keys_folder_path, file_name) == '0o400'

    clean_builder_folder(my_folder_path)


def test_builder_existing_mnemonic_cli_flag_with_password_confirmation() -> None:
    # Prepare folder
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    runner = CliRunner()
    withdrawal_address = '0x00000000219ab540356cBB839Cbe05303d7705Fa'
    inputs = [
        'english',  # top-level CLI language
        'TREZOR',  # repeat the --mnemonic_password value for confirmation
        '0', '0',  # builder_start_index + confirm (mnemonic is already known)
        '1',  # num_builders
        'mainnet',  # chain
        'MyPasswordIs', 'MyPasswordIs',
        withdrawal_address, withdrawal_address,
        '1',  # builder_amount
    ]
    data = '\n'.join(inputs)
    arguments = [
        '--ignore_connectivity',
        'builder',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--mnemonic_password', 'TREZOR',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments, input=data)
    assert result.exit_code == 0

    builder_keys_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(builder_keys_folder_path))

    all_uuid = [
        get_uuid(builder_keys_folder_path + '/' + key_file)
        for key_file in key_files
        if key_file.startswith('keystore')
    ]
    assert len(set(all_uuid)) == 1

    clean_builder_folder(my_folder_path)


def test_builder_mnemonic_password_requires_existing_mnemonic() -> None:
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    runner = CliRunner()
    inputs = [
        'english',  # top-level CLI language
        'no',  # no existing mnemonic
        'TREZOR',  # repeat the --mnemonic_password value for confirmation
    ]
    data = '\n'.join(inputs)
    arguments = [
        '--ignore_connectivity',
        'builder',
        '--mnemonic_password', 'TREZOR',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments, input=data)
    assert result.exit_code == 1
    assert 'not allowed when generating a new mnemonic' in str(result.exception)

    clean_builder_folder(my_folder_path)


def test_builder_non_interactive() -> None:
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    runner = CliRunner()
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'builder',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--builder_start_index', '0',
        '--num_builders', '1',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--builder_amount', '1',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments)
    assert result.exit_code == 0

    builder_keys_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(builder_keys_folder_path))
    assert len([f for f in key_files if f.startswith('keystore')]) == 1
    assert len([f for f in key_files if f.startswith('builder_deposit_data')]) == 1

    clean_builder_folder(my_folder_path)


def test_builder_amount_below_minimum_rejected() -> None:
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    runner = CliRunner()
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'builder',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--builder_start_index', '0',
        '--num_builders', '1',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--builder_amount', '0.5',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments)
    assert result.exit_code == 1

    builder_keys_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    assert not os.path.exists(builder_keys_folder_path)

    clean_builder_folder(my_folder_path)


@pytest.mark.parametrize('builder_amount', ['1', '2048', '1000000'])
def test_builder_amount_has_no_upper_bound(builder_amount: str) -> None:
    # Unlike validator deposits (capped at 2048 ETH on mainnet), builder deposits have no maximum.
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    runner = CliRunner()
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'builder',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--builder_start_index', '0',
        '--num_builders', '1',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--builder_amount', builder_amount,
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments)
    assert result.exit_code == 0

    builder_keys_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(builder_keys_folder_path))
    deposit_file = [key_file for key_file in key_files if key_file.startswith('builder_deposit_data')][0]
    with open(builder_keys_folder_path + '/' + deposit_file, encoding='utf-8') as f:
        deposits_dict = json.load(f)
    for deposit in deposits_dict:
        assert deposit['amount'] == int(float(builder_amount) * ETH2GWEI)

    clean_builder_folder(my_folder_path)


def test_builder_gnosis_chain_amount_is_not_multiplied() -> None:
    # Unlike validator deposits, builder amounts are not scaled by the chain's MULTIPLIER,
    # since builder deposit handling by non-mainnet-derived chains is not yet defined.
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    runner = CliRunner()
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'builder',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--builder_start_index', '0',
        '--num_builders', '1',
        '--chain', 'gnosis',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--builder_amount', '1',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments)
    assert result.exit_code == 0

    builder_keys_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(builder_keys_folder_path))
    deposit_file = [key_file for key_file in key_files if key_file.startswith('builder_deposit_data')][0]
    with open(builder_keys_folder_path + '/' + deposit_file, encoding='utf-8') as f:
        deposits_dict = json.load(f)
    for deposit in deposits_dict:
        assert deposit['amount'] == ETH2GWEI

    clean_builder_folder(my_folder_path)


def test_builder_custom_devnet_chain() -> None:
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    devnet_chain = {
        "network_name": "hoodicopy",
        "genesis_fork_version": "20000910",
        "exit_fork_version": "04017000",
        "genesis_validator_root": "212f13fc4df078b6cb7db228f1c8307566dcecf900867401a92023d7ba99cb5f"
    }
    devnet_chain_setting = json.dumps(devnet_chain)

    runner = CliRunner()
    withdrawal_address = '0x00000000219ab540356cBB839Cbe05303d7705Fa'
    inputs = [
        'english',
        '0', '0',  # builder_start_index + confirm
        '1',  # num_builders
        'MyPasswordIs', 'MyPasswordIs',
        withdrawal_address, withdrawal_address,
        '1',  # builder_amount
    ]
    data = '\n'.join(inputs)
    arguments = [
        '--ignore_connectivity',
        'builder',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--devnet_chain_setting', devnet_chain_setting,
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments, input=data)
    assert result.exit_code == 0

    builder_keys_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(builder_keys_folder_path))
    assert len([f for f in key_files if f.startswith('keystore')]) == 1

    clean_builder_folder(my_folder_path)


def test_builder_withdrawal_address_bad_checksum() -> None:
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    runner = CliRunner()

    # NOTE: final 'A' needed to be an 'a'
    wrong_withdrawal_address = '0x00000000219ab540356cBB839Cbe05303d7705FA'
    correct_withdrawal_address = '0x00000000219ab540356cBB839Cbe05303d7705Fa'

    inputs = [
        'english',
        '0', '0',
        '1',
        'mainnet',
        'MyPasswordIs', 'MyPasswordIs',
        wrong_withdrawal_address, correct_withdrawal_address, correct_withdrawal_address,
        '1',
    ]
    data = '\n'.join(inputs)
    arguments = [
        '--ignore_connectivity',
        'builder',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments, input=data)
    assert result.exit_code == 0

    builder_keys_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(builder_keys_folder_path))
    deposit_file = [key_file for key_file in key_files if key_file.startswith('builder_deposit_data')][0]
    with open(builder_keys_folder_path + '/' + deposit_file, encoding='utf-8') as f:
        deposits_dict = json.load(f)
    for deposit in deposits_dict:
        withdrawal_credentials = bytes.fromhex(deposit['withdrawal_credentials'])
        assert withdrawal_credentials == (
            BUILDER_WITHDRAWAL_PREFIX + b'\x00' * 11 + decode_hex(correct_withdrawal_address)
        )

    clean_builder_folder(my_folder_path)


def test_builder_missing_withdrawal_address_non_interactive_fails() -> None:
    # Builders have no BLS-only withdrawal type, so an withdrawal address is always required.
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    runner = CliRunner()
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'builder',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--builder_start_index', '0',
        '--num_builders', '1',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--builder_amount', '1',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments)
    assert result.exit_code == 1

    builder_keys_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    assert not os.path.exists(builder_keys_folder_path)

    clean_builder_folder(my_folder_path)


def test_pbkdf2_builder() -> None:
    # Prepare pbkdf2 folder
    pbkdf2_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_builder_folder(pbkdf2_folder_path)
    if not os.path.exists(pbkdf2_folder_path):
        os.mkdir(pbkdf2_folder_path)

    # Prepare scrypt folder
    scrypt_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER_2')
    clean_builder_folder(scrypt_folder_path)
    if not os.path.exists(scrypt_folder_path):
        os.mkdir(scrypt_folder_path)

    common_arguments = [
        '--language', 'english',
        '--non_interactive',
        'builder',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--builder_start_index', '0',
        '--num_builders', '1',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--builder_amount', '1',
    ]

    runner = CliRunner()
    result = runner.invoke(cli, common_arguments + ['--folder', pbkdf2_folder_path, '--pbkdf2'])
    assert result.exit_code == 0
    result = runner.invoke(cli, common_arguments + ['--folder', scrypt_folder_path])
    assert result.exit_code == 0

    pbkdf2_builder_folder = os.path.join(pbkdf2_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    keystore_file = [f for f in os.listdir(pbkdf2_builder_folder) if f.startswith('keystore')][0]
    with open(os.path.join(pbkdf2_builder_folder, keystore_file), encoding='utf-8') as f:
        pbkdf2_keystore_dict = json.load(f)

    scrypt_builder_folder = os.path.join(scrypt_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    keystore_file = [f for f in os.listdir(scrypt_builder_folder) if f.startswith('keystore')][0]
    with open(os.path.join(scrypt_builder_folder, keystore_file), encoding='utf-8') as f:
        scrypt_keystore_dict = json.load(f)

    assert pbkdf2_keystore_dict['crypto']['kdf']['function'] == 'pbkdf2'
    assert scrypt_keystore_dict['crypto']['kdf']['function'] == 'scrypt'
    assert pbkdf2_keystore_dict['pubkey'] == scrypt_keystore_dict['pubkey']

    clean_builder_folder(pbkdf2_folder_path)
    clean_builder_folder(scrypt_folder_path)
