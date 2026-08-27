import os

from ethstaker_deposit.utils.constants import (
    DEFAULT_BLS_TO_EXECUTION_CHANGES_FOLDER_NAME,
    DEFAULT_BLS_TO_EXECUTION_CHANGES_KEYSTORE_FOLDER_NAME,
    DEFAULT_BUILDER_KEYS_FOLDER_NAME,
    DEFAULT_EXIT_TRANSACTION_FOLDER_NAME,
    DEFAULT_PARTIAL_DEPOSIT_FOLDER_NAME,
    DEFAULT_VALIDATOR_KEYS_FOLDER_NAME,
)
from tests.shared_helpers import clean_folder


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


def prepare_testing_folder(os_ref, testing_folder_name='TESTING_TEMP_FOLDER'):
    my_folder_path = os_ref.path.join(os_ref.getcwd(), testing_folder_name)
    clean_btec_folder(my_folder_path)
    if not os_ref.path.exists(my_folder_path):
        os_ref.mkdir(my_folder_path)
    return my_folder_path
