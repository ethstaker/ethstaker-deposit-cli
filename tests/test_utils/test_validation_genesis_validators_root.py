import pytest

from ethstaker_deposit.credentials import Credential
from ethstaker_deposit.exceptions import ValidationError
from ethstaker_deposit.settings import EphemerySetting, MainnetSetting
from ethstaker_deposit.utils.exit_transaction import exit_transaction_generation
from ethstaker_deposit.utils.validation import (
    validate_bls_to_execution_change_keystore,
    validate_genesis_validators_root,
    validate_signed_exit,
)


MNEMONIC = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
ADDRESS = '0x00000000219ab540356cBB839Cbe05303d7705Fa'

# Ephemery deliberately carries no GENESIS_VALIDATORS_ROOT; the root changes with each reset.
LOCALIZED = 'GENESIS_VALIDATORS_ROOT'
HARDCODED = 'genesis validators root should NOT be empty'


def _credential(chain_setting) -> Credential:
    return Credential(
        mnemonic=MNEMONIC,
        mnemonic_password='',
        index=0,
        amount=32 * 10**9,
        chain_setting=chain_setting,
        hex_withdrawal_address=ADDRESS,
    )


def test_validate_genesis_validators_root_rejects_missing_root() -> None:
    with pytest.raises(ValidationError, match=LOCALIZED):
        validate_genesis_validators_root(EphemerySetting)


def test_validate_genesis_validators_root_accepts_present_root() -> None:
    assert validate_genesis_validators_root(MainnetSetting) is None


def test_exit_transaction_generation_rejects_missing_root() -> None:
    with pytest.raises(ValidationError, match=HARDCODED):
        exit_transaction_generation(
            chain_setting=EphemerySetting,
            signing_key=_credential(EphemerySetting).signing_sk,
            validator_index=7,
            epoch=1,
        )


def test_validate_signed_exit_rejects_missing_root() -> None:
    with pytest.raises(ValidationError, match=LOCALIZED):
        validate_signed_exit(
            validator_index='7',
            epoch='1',
            signature='0x' + '00' * 96,
            pubkey='00' * 48,
            chain_setting=EphemerySetting,
        )


def test_validate_bls_to_execution_change_keystore_rejects_missing_root() -> None:
    with pytest.raises(ValidationError, match=LOCALIZED):
        validate_bls_to_execution_change_keystore(
            validator_index='7',
            to_execution_address=ADDRESS,
            signature='0x' + '00' * 96,
            pubkey='00' * 48,
            chain_setting=EphemerySetting,
        )


def test_get_bls_to_execution_change_dict_rejects_missing_root() -> None:
    with pytest.raises(ValidationError, match=HARDCODED):
        _credential(EphemerySetting).get_bls_to_execution_change_dict(validator_index=7)
