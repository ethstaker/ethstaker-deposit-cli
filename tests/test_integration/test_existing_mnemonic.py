import os
import pytest
from ethstaker_deposit.utils.constants import DEFAULT_VALIDATOR_KEYS_FOLDER_NAME
from tests.shared_helpers import get_permissions
from tests.test_integration.helpers import run_deposit_cli, run_deposit_cli_capture


@pytest.mark.asyncio
async def test_script(deposit_cli_installed, cli_output_folder) -> None:
    my_folder_path = cli_output_folder
    cmd_args = [
        '--language', 'english',
        '--non_interactive',
        'existing-mnemonic',
        '--num_validators', '1',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--mnemonic_password', 'TREZOR',
        '--validator_start_index', '1',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--folder', my_folder_path,
    ]
    await run_deposit_cli(*cmd_args)

    # Check files
    validator_keys_folder_path = os.path.join(my_folder_path, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(validator_keys_folder_path))

    # Verify file permissions
    if os.name == 'posix':
        for file_name in key_files:
            assert get_permissions(validator_keys_folder_path, file_name) == '0o400'


@pytest.mark.asyncio
async def test_script_abbreviated_mnemonic(deposit_cli_installed, cli_output_folder) -> None:
    my_folder_path = cli_output_folder
    cmd_args = [
        '--language', 'english',
        '--non_interactive',
        'existing-mnemonic',
        '--num_validators', '1',
        '--mnemonic', 'aban aban aban aban aban aban aban aban aban aban aban abou',
        '--mnemonic_password', 'TREZOR',
        '--validator_start_index', '1',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--folder', my_folder_path,
    ]
    await run_deposit_cli(*cmd_args)

    # Check files
    validator_keys_folder_path = os.path.join(my_folder_path, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(validator_keys_folder_path))

    # Verify file permissions
    if os.name == 'posix':
        for file_name in key_files:
            assert get_permissions(validator_keys_folder_path, file_name) == '0o400'


def test_script_invalid_checksum(deposit_cli_installed, cli_output_folder) -> None:
    # A bad withdrawal-address checksum must exit non-zero and create no keystores.
    my_folder_path = cli_output_folder

    result = run_deposit_cli_capture(
        '--language', 'english',
        '--non_interactive',
        'existing-mnemonic',
        '--num_validators', '1',
        '--mnemonic', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '--validator_start_index', '0',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa1234',
        '--folder', my_folder_path,
    )

    assert result.returncode == 1
    assert b'Error' in result.stderr
    assert not os.path.exists(os.path.join(my_folder_path, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME))


def test_script_invalid_mnemonic(deposit_cli_installed, cli_output_folder) -> None:
    # An invalid mnemonic must exit non-zero and create no keystores.
    my_folder_path = cli_output_folder

    result = run_deposit_cli_capture(
        '--language', 'english',
        '--non_interactive',
        'existing-mnemonic',
        '--num_validators', '1',
        '--mnemonic', 'this is not a valid mnemonic phrase at all',
        '--validator_start_index', '0',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--folder', my_folder_path,
    )

    assert result.returncode == 1
    assert b'Error' in result.stderr
    assert not os.path.exists(os.path.join(my_folder_path, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME))
