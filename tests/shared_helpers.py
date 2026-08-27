import json
import os
import shutil
import stat
import sys

from ethstaker_deposit.credentials import Credential
from ethstaker_deposit.key_handling.keystore import Keystore
from ethstaker_deposit.settings import DEPOSIT_CLI_VERSION, BaseChainSetting
from ethstaker_deposit.utils.constants import ETH2GWEI
from ethstaker_deposit.utils.validation import verify_bls_to_execution_change_json


def remove_readonly(func, path, exc_info_or_exc):
    # Used on Windows to force deleting directories with read-only files in them
    # created by our sensitive_opener.
    os.chmod(path, stat.S_IWRITE)
    func(path)


rmtree_kwargs = {}
if sys.version_info >= (3, 12):
    rmtree_kwargs['onexc'] = remove_readonly
else:
    rmtree_kwargs['onerror'] = remove_readonly


def clean_folder(primary_folder_path: str, sub_folder_path: str, ignore_primary: bool = False) -> None:
    if not os.path.exists(sub_folder_path):
        return

    shutil.rmtree(sub_folder_path, **rmtree_kwargs)
    if not ignore_primary:
        shutil.rmtree(primary_folder_path, **rmtree_kwargs)


def get_uuid(key_file: str) -> str:
    keystore = Keystore.from_file(key_file)
    return keystore.uuid


def get_permissions(path: str, file_name: str) -> str:
    return oct(os.stat(os.path.join(path, file_name)).st_mode & 0o777)


def verify_file_permission(os_ref, folder_path, files):
    if os_ref.name == 'posix':
        for file_name in files:
            assert get_permissions(folder_path, file_name) == '0o400'


def read_json_file(path: str, file_name: str):
    with open(os.path.join(path, file_name), encoding='utf-8') as f:
        return json.load(f)


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
