import json
import os

from ethstaker_deposit.utils.file_handling import (
    sensitive_opener,
)


def export_deposit_data_json(folder: str, timestamp: float, deposit_data: list[dict[str, bytes]]) -> str:
    file_folder = os.path.join(folder, f'deposit_data-{int(timestamp)}.json')
    with open(file_folder, 'w', encoding='utf-8', opener=sensitive_opener) as f:
        json.dump(deposit_data, f, default=lambda x: x.hex())
    return file_folder


def export_builder_deposit_data_json(folder: str, timestamp: float,
                                     builder_deposit_data: list[dict[str, bytes]]) -> str:
    file_folder = os.path.join(folder, f'builder_deposit_data-{int(timestamp)}.json')
    with open(file_folder, 'w', encoding='utf-8', opener=sensitive_opener) as f:
        json.dump(builder_deposit_data, f, default=lambda x: x.hex())
    return file_folder
