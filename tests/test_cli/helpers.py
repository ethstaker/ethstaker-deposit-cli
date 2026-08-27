import json
import os
import shutil
import sys
import stat

from ethstaker_deposit.key_handling.keystore import Keystore
from ethstaker_deposit.utils.constants import (
    DEFAULT_BLS_TO_EXECUTION_CHANGES_FOLDER_NAME,
    DEFAULT_BLS_TO_EXECUTION_CHANGES_KEYSTORE_FOLDER_NAME,
    DEFAULT_BUILDER_KEYS_FOLDER_NAME,
    DEFAULT_EXIT_TRANSACTION_FOLDER_NAME,
    DEFAULT_PARTIAL_DEPOSIT_FOLDER_NAME,
    DEFAULT_VALIDATOR_KEYS_FOLDER_NAME,
)


def clean_key_folder(my_folder_path: str) -> None:
    sub_folder_path = os.path.join(my_folder_path, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    clean_folder(my_folder_path, sub_folder_path)


def clean_builder_folder(my_folder_path: str) -> None:
    sub_folder_path = os.path.join(my_folder_path, DEFAULT_BUILDER_KEYS_FOLDER_NAME)
    clean_folder(my_folder_path, sub_folder_path)


def clean_partial_deposit_folder(my_folder_path: str) -> None:
    sub_folder_path = os.path.join(my_folder_path, DEFAULT_PARTIAL_DEPOSIT_FOLDER_NAME)
    clean_folder(my_folder_path, sub_folder_path)


def clean_btec_folder(my_folder_path: str) -> None:
    sub_folder_path = os.path.join(my_folder_path, DEFAULT_BLS_TO_EXECUTION_CHANGES_FOLDER_NAME)
    clean_folder(my_folder_path, sub_folder_path)


def clean_btec_keystore_folder(my_folder_path: str) -> None:
    sub_folder_path = os.path.join(my_folder_path, DEFAULT_BLS_TO_EXECUTION_CHANGES_KEYSTORE_FOLDER_NAME)
    clean_folder(my_folder_path, sub_folder_path)


def clean_exit_transaction_folder(my_folder_path: str) -> None:
    sub_folder_path = os.path.join(my_folder_path, DEFAULT_EXIT_TRANSACTION_FOLDER_NAME)
    clean_folder(my_folder_path, sub_folder_path)


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


def prepare_testing_folder(os_ref, testing_folder_name='TESTING_TEMP_FOLDER'):
    my_folder_path = os_ref.path.join(os_ref.getcwd(), testing_folder_name)
    clean_btec_folder(my_folder_path)
    if not os_ref.path.exists(my_folder_path):
        os_ref.mkdir(my_folder_path)
    return my_folder_path


def read_json_file(path: str, file_name: str):
    with open(os.path.join(path, file_name), encoding='utf-8') as f:
        return json.load(f)
