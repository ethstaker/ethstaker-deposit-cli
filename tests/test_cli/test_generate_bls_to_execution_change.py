import os
import json

from click.testing import CliRunner

from ethstaker_deposit.credentials import Credential
from ethstaker_deposit.deposit import cli
from ethstaker_deposit.settings import DEPOSIT_CLI_VERSION, BaseChainSetting, MainnetSetting
from ethstaker_deposit.utils.constants import DEFAULT_BLS_TO_EXECUTION_CHANGES_FOLDER_NAME, ETH2GWEI
from ethstaker_deposit.utils.validation import verify_bls_to_execution_change_json
from .helpers import (
    clean_btec_folder,
    prepare_testing_folder,
    read_json_file,
    verify_file_permission,
)

TEST_MNEMONIC = (
    'sister protect peanut hill ready work profit fit wish want small inflict flip member tail between sick '
    'setup bright duck morning sell paper worry'
)


def assert_btec_content(
        folder_path: str,
        expected_validator_indices: list[int],
        expected_network: str = 'mainnet',
        expected_withdrawal_address: str = '0x3434343434343434343434343434343434343434',
) -> str:
    _, _, btec_files = next(os.walk(folder_path))
    assert len(btec_files) == 1
    btec_data = read_json_file(folder_path, btec_files[0])
    assert [int(change['message']['validator_index']) for change in btec_data] == expected_validator_indices
    for change in btec_data:
        assert change['message']['from_bls_pubkey'].startswith('0x')
        assert len(change['message']['from_bls_pubkey']) == 2 + 48 * 2
        assert change['message']['to_execution_address'] == expected_withdrawal_address.lower()
        assert len(change['signature']) == 2 + 96 * 2
        assert change['metadata']['network_name'] == expected_network
        assert change['metadata']['deposit_cli_version'] == DEPOSIT_CLI_VERSION
        assert len(change['metadata']['genesis_validators_root']) == 2 + 32 * 2
    return os.path.join(folder_path, btec_files[0])


def assert_btec_round_trip(
        filefolder: str,
        *,
        mnemonic: str,
        start_index: int,
        validator_indices: list[int],
        withdrawal_address: str,
        chain_setting: BaseChainSetting,
) -> None:
    credentials = [
        Credential(
            mnemonic=mnemonic,
            mnemonic_password='',
            index=index,
            amount=chain_setting.MIN_ACTIVATION_AMOUNT * chain_setting.MULTIPLIER * ETH2GWEI,
            chain_setting=chain_setting,
            hex_withdrawal_address=withdrawal_address,
        )
        for index in range(start_index, start_index + len(validator_indices))
    ]
    assert verify_bls_to_execution_change_json(
        filefolder,
        credentials,
        input_validator_indices=validator_indices,
        input_withdrawal_address=withdrawal_address,
        chain_setting=chain_setting,
    )


def test_existing_mnemonic_bls_withdrawal() -> None:
    # Prepare folder
    my_folder_path = prepare_testing_folder(os)

    runner = CliRunner()
    inputs = []
    data = '\n'.join(inputs)
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'generate-bls-to-execution-change',
        '--bls_to_execution_changes_folder', my_folder_path,
        '--chain', 'mainnet',
        '--mnemonic', 'sister protect peanut hill ready work profit fit wish want small inflict flip member tail between sick setup bright duck morning sell paper worry',  # noqa: E501
        '--bls_withdrawal_credentials_list', '0x00bd0b5a34de5fb17df08410b5e615dda87caf4fb72d0aac91ce5e52fc6aa8de',
        '--validator_start_index', '0',
        '--validator_indices', '1',
        '--withdrawal_address', '0x3434343434343434343434343434343434343434',
    ]
    result = runner.invoke(cli, arguments, input=data)
    assert result.exit_code == 0

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

    # Clean up
    clean_btec_folder(my_folder_path)


def test_existing_mnemonic_bls_withdrawal_interactive() -> None:
    # Prepare folder
    my_folder_path = prepare_testing_folder(os)

    runner = CliRunner()
    inputs = [
        'mainnet',  # network/chain
        'sister protect peanut hill ready work profit fit wish want small inflict flip member tail between sick setup bright duck morning sell paper worry',  # noqa: E501
        '0',  # validator_start_index
        '1',  # validator_index
        '0x00bd0b5a34de5fb17df08410b5e615dda87caf4fb72d0aac91ce5e52fc6aa8de',
        '0x3434343434343434343434343434343434343434',
        '0x3434343434343434343434343434343434343434',

    ]
    data = '\n'.join(inputs)
    arguments = [
        '--language', 'english',
        '--ignore_connectivity',
        'generate-bls-to-execution-change',
        '--bls_to_execution_changes_folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments, input=data)
    assert result.exit_code == 0

    # Check files
    bls_to_execution_changes_folder_path = os.path.join(my_folder_path, DEFAULT_BLS_TO_EXECUTION_CHANGES_FOLDER_NAME)
    _, _, btec_files = next(os.walk(bls_to_execution_changes_folder_path))

    assert_btec_content(bls_to_execution_changes_folder_path, [1])

    # Verify file permissions
    verify_file_permission(os, folder_path=bls_to_execution_changes_folder_path, files=btec_files)

    # Clean up
    clean_btec_folder(my_folder_path)


def test_existing_mnemonic_bls_withdrawal_multiple() -> None:
    # Prepare folder
    my_folder_path = prepare_testing_folder(os)

    runner = CliRunner()
    inputs = []
    data = '\n'.join(inputs)
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'generate-bls-to-execution-change',
        '--bls_to_execution_changes_folder', my_folder_path,
        '--chain', 'mainnet',
        '--mnemonic', 'sister protect peanut hill ready work profit fit wish want small inflict flip member tail between sick setup bright duck morning sell paper worry',  # noqa: E501
        '--bls_withdrawal_credentials_list', '0x00bd0b5a34de5fb17df08410b5e615dda87caf4fb72d0aac91ce5e52fc6aa8de, 0x00a75d83f169fa6923f3dd78386d9608fab710d8f7fcf71ba9985893675d5382',  # noqa: E501
        '--validator_start_index', '0',
        '--validator_indices', '1,2',
        '--withdrawal_address', '0x3434343434343434343434343434343434343434',
    ]
    result = runner.invoke(cli, arguments, input=data)
    assert result.exit_code == 0

    # Check files
    bls_to_execution_changes_folder_path = os.path.join(my_folder_path, DEFAULT_BLS_TO_EXECUTION_CHANGES_FOLDER_NAME)
    _, _, btec_files = next(os.walk(bls_to_execution_changes_folder_path))

    btec_file = assert_btec_content(bls_to_execution_changes_folder_path, [1, 2])
    assert_btec_round_trip(
        btec_file,
        mnemonic=TEST_MNEMONIC,
        start_index=0,
        validator_indices=[1, 2],
        withdrawal_address='0x3434343434343434343434343434343434343434',
        chain_setting=MainnetSetting,
    )

    # Verify file permissions
    verify_file_permission(os, folder_path=bls_to_execution_changes_folder_path, files=btec_files)

    # Clean up
    clean_btec_folder(my_folder_path)


def test_bls_change_custom_testnet() -> None:
    # Prepare folder
    my_folder_path = prepare_testing_folder(os)

    devnet_chain = {
        "network_name": "hoodicopy",
        "genesis_fork_version": "20000910",
        "exit_fork_version": "04017000",
        "genesis_validator_root": "212f13fc4df078b6cb7db228f1c8307566dcecf900867401a92023d7ba99cb5f"
    }

    devnet_chain_setting = json.dumps(devnet_chain)

    runner = CliRunner()
    inputs = []
    data = '\n'.join(inputs)
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'generate-bls-to-execution-change',
        '--bls_to_execution_changes_folder', my_folder_path,
        '--devnet_chain_setting', devnet_chain_setting,
        '--mnemonic', 'sister protect peanut hill ready work profit fit wish want small inflict flip member tail between sick setup bright duck morning sell paper worry',  # noqa: E501
        '--bls_withdrawal_credentials_list', '0x00bd0b5a34de5fb17df08410b5e615dda87caf4fb72d0aac91ce5e52fc6aa8de',
        '--validator_start_index', '0',
        '--validator_indices', '1',
        '--withdrawal_address', '0x3434343434343434343434343434343434343434',
    ]
    result = runner.invoke(cli, arguments, input=data)
    assert result.exit_code == 0

    # Check files
    bls_to_execution_changes_folder_path = os.path.join(my_folder_path, DEFAULT_BLS_TO_EXECUTION_CHANGES_FOLDER_NAME)
    _, _, btec_files = next(os.walk(bls_to_execution_changes_folder_path))

    btec_file = assert_btec_content(
        bls_to_execution_changes_folder_path,
        [1],
        expected_network='hoodicopy',
    )
    assert_btec_round_trip(
        btec_file,
        mnemonic=TEST_MNEMONIC,
        start_index=0,
        validator_indices=[1],
        withdrawal_address='0x3434343434343434343434343434343434343434',
        chain_setting=BaseChainSetting(
            NETWORK_NAME='hoodicopy',
            GENESIS_FORK_VERSION=bytes.fromhex('20000910'),
            EXIT_FORK_VERSION=bytes.fromhex('04017000'),
            GENESIS_VALIDATORS_ROOT=bytes.fromhex(
                '212f13fc4df078b6cb7db228f1c8307566dcecf900867401a92023d7ba99cb5f'
            ),
        ),
    )

    # Verify file permissions
    verify_file_permission(os, folder_path=bls_to_execution_changes_folder_path, files=btec_files)

    # Clean up
    clean_btec_folder(my_folder_path)
