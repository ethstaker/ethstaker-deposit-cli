from copy import deepcopy

import pytest

from ethstaker_deposit.credentials import Credential
from ethstaker_deposit.exceptions import ValidationError
from ethstaker_deposit.settings import EphemerySetting, MainnetSetting
from ethstaker_deposit.utils.validation import validate_bls_to_execution_change


MNEMONIC = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
ADDRESS = '0x00000000219ab540356cBB839Cbe05303d7705Fa'


@pytest.fixture
def btec_case() -> tuple[Credential, dict[str, object]]:
    credential = Credential(
        mnemonic=MNEMONIC,
        mnemonic_password='',
        index=0,
        amount=32 * 10**9,
        chain_setting=MainnetSetting,
        hex_withdrawal_address=ADDRESS,
    )
    return credential, credential.get_bls_to_execution_change_dict(validator_index=7)


def test_validate_bls_to_execution_change_accepts_generated_change(btec_case) -> None:
    credential, btec = btec_case
    assert validate_bls_to_execution_change(
        btec,
        credential,
        input_validator_index=7,
        input_withdrawal_address=ADDRESS,
        chain_setting=MainnetSetting,
    )


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('validator_index', '8'),
        ('from_bls_pubkey', '0x' + '11' * 48),
        ('to_execution_address', '0x' + '22' * 20),
    ],
)
def test_validate_bls_to_execution_change_rejects_message_mismatch(btec_case, field, value) -> None:
    credential, btec = btec_case
    changed = deepcopy(btec)
    changed['message'][field] = value
    assert not validate_bls_to_execution_change(
        changed,
        credential,
        input_validator_index=7,
        input_withdrawal_address=ADDRESS,
        chain_setting=MainnetSetting,
    )


def test_validate_bls_to_execution_change_rejects_wrong_input_address(btec_case) -> None:
    credential, btec = btec_case
    assert not validate_bls_to_execution_change(
        btec,
        credential,
        input_validator_index=7,
        input_withdrawal_address='0x1111111111111111111111111111111111111111',
        chain_setting=MainnetSetting,
    )


def test_validate_bls_to_execution_change_rejects_wrong_root_or_signature(btec_case) -> None:
    credential, btec = btec_case
    wrong_root = deepcopy(btec)
    wrong_root['metadata']['genesis_validators_root'] = '0x' + '00' * 32
    assert not validate_bls_to_execution_change(
        wrong_root,
        credential,
        input_validator_index=7,
        input_withdrawal_address=ADDRESS,
        chain_setting=MainnetSetting,
    )

    wrong_signature = deepcopy(btec)
    wrong_signature['signature'] = '0x' + '00' * 96
    assert not validate_bls_to_execution_change(
        wrong_signature,
        credential,
        input_validator_index=7,
        input_withdrawal_address=ADDRESS,
        chain_setting=MainnetSetting,
    )


def test_get_bls_to_execution_change_rejects_missing_genesis_root() -> None:
    credential = Credential(
        mnemonic=MNEMONIC,
        mnemonic_password='',
        index=0,
        amount=32 * 10**9,
        chain_setting=EphemerySetting,
        hex_withdrawal_address=ADDRESS,
    )
    with pytest.raises(ValidationError, match='genesis validators root should NOT be empty'):
        credential.get_bls_to_execution_change(validator_index=7)
