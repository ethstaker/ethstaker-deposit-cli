import json
import os

from ethstaker_deposit.utils.file_handling import (
    sensitive_opener,
)


def _export_json(folder: str, timestamp: float, prefix: str, data: list[dict[str, bytes]]) -> str:
    file_folder = os.path.join(folder, f'{prefix}-{int(timestamp)}.json')
    with open(file_folder, 'w', encoding='utf-8', opener=sensitive_opener) as f:
        json.dump(data, f, default=lambda x: x.hex())
    return file_folder


def export_deposit_data_json(folder: str, timestamp: float, deposit_data: list[dict[str, bytes]]) -> str:
    return _export_json(folder, timestamp, 'deposit_data', deposit_data)


def export_builder_deposit_data_json(folder: str, timestamp: float,
                                     builder_deposit_data: list[dict[str, bytes]]) -> str:
    return _export_json(folder, timestamp, 'builder_deposit_data', builder_deposit_data)
