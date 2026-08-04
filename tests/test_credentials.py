import json
import os

import pytest
from py_ecc.bls import G2ProofOfPossession as bls

from ethstaker_deposit.credentials import Credential, CredentialList
from ethstaker_deposit.settings import DEPOSIT_CLI_VERSION, MainnetSetting
from ethstaker_deposit.utils.constants import (
    BLS_WITHDRAWAL_PREFIX,
    COMPOUNDING_WITHDRAWAL_PREFIX,
    EXECUTION_ADDRESS_WITHDRAWAL_PREFIX,
    ETH2GWEI,
    MAX_DEPOSIT_AMOUNT,
)
from ethstaker_deposit.utils.ssz import (
    SignedVoluntaryExit,
    VoluntaryExit,
    compute_deposit_domain,
    compute_signing_root,
    compute_voluntary_exit_domain,
)
from ethstaker_deposit.utils.crypto import SHA256
from ethstaker_deposit.utils.validation import validate_deposit
from ethstaker_deposit.exceptions import ValidationError


MNEMONIC = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
WITHDRAWAL_ADDRESS = '0x00000000219ab540356cBB839Cbe05303d7705Fa'


def make_credential(*, address: str | None = WITHDRAWAL_ADDRESS, compounding: bool = False) -> Credential:
    return Credential(
        mnemonic=MNEMONIC,
        mnemonic_password='',
        index=0,
        amount=32 * ETH2GWEI,
        chain_setting=MainnetSetting,
        hex_withdrawal_address=address,
        compounding=compounding,
    )


def test_from_mnemonic() -> None:
    with pytest.raises(ValueError):
        CredentialList.from_mnemonic(
            mnemonic='',
            mnemonic_password='',
            num_keys=1,
            amounts=[32, 32],
            chain_setting=MainnetSetting,
            start_index=1,
            hex_withdrawal_address=None,
            compounding=False,
        )


def test_credential_withdrawal_credentials_variants() -> None:
    bls_credential = make_credential(address=None)
    execution_credential = make_credential()
    compounding_credential = make_credential(compounding=True)

    assert bls_credential.withdrawal_prefix == BLS_WITHDRAWAL_PREFIX
    assert bls_credential.withdrawal_type.name == 'BLS_WITHDRAWAL'
    assert len(bls_credential.withdrawal_credentials) == 32
    assert bls_credential.withdrawal_credentials[1:] == SHA256(bls_credential.withdrawal_pk)[1:]

    assert execution_credential.withdrawal_prefix == EXECUTION_ADDRESS_WITHDRAWAL_PREFIX
    assert execution_credential.withdrawal_credentials == (
        EXECUTION_ADDRESS_WITHDRAWAL_PREFIX + b'\x00' * 11 + execution_credential.withdrawal_address
    )
    assert compounding_credential.withdrawal_prefix == COMPOUNDING_WITHDRAWAL_PREFIX
    assert compounding_credential.withdrawal_credentials == (
        COMPOUNDING_WITHDRAWAL_PREFIX + b'\x00' * 11 + compounding_credential.withdrawal_address
    )


def test_signed_deposit_and_datum_validate() -> None:
    credential = make_credential()
    signed_deposit = credential.signed_deposit
    domain = compute_deposit_domain(MainnetSetting.GENESIS_FORK_VERSION)
    assert bls.Verify(
        credential.signing_pk,
        compute_signing_root(credential.deposit_message, domain),
        signed_deposit.signature,
    )

    datum = credential.deposit_datum_dict
    assert datum['deposit_message_root'] == credential.deposit_message.hash_tree_root
    assert datum['deposit_data_root'] == signed_deposit.hash_tree_root
    assert datum['fork_version'] == MainnetSetting.GENESIS_FORK_VERSION
    assert datum['network_name'] == MainnetSetting.NETWORK_NAME
    assert datum['deposit_cli_version'] == DEPOSIT_CLI_VERSION

    json_datum = json.loads(json.dumps(datum, default=lambda value: value.hex()))
    assert validate_deposit(json_datum, MainnetSetting, credential)


@pytest.mark.parametrize('amount', [0, MAX_DEPOSIT_AMOUNT + 1])
def test_deposit_message_rejects_invalid_amount(amount: int) -> None:
    credential = make_credential()
    credential.amount = amount
    with pytest.raises(ValidationError, match='deposits are not within the bounds'):
        _ = credential.deposit_message


def test_save_exit_transaction_writes_signed_json(tmp_path) -> None:
    credential = make_credential(address=None)
    filepath = credential.save_exit_transaction(
        validator_index=7,
        epoch=42,
        folder=str(tmp_path),
        timestamp=1234567890,
    )

    assert filepath == os.path.join(str(tmp_path), 'signed_exit_transaction-7-1234567890.json')
    with open(filepath, encoding='utf-8') as file:
        result = json.load(file)
    assert result['message'] == {'epoch': '42', 'validator_index': '7'}
    assert result['signature'].startswith('0x')
    assert len(result['signature']) == 2 + 96 * 2

    message = VoluntaryExit(epoch=42, validator_index=7)
    domain = compute_voluntary_exit_domain(
        MainnetSetting.EXIT_FORK_VERSION,
        MainnetSetting.GENESIS_VALIDATORS_ROOT,
    )
    signed_exit = SignedVoluntaryExit(message=message, signature=bytes.fromhex(result['signature'][2:]))
    assert bls.Verify(credential.signing_pk, compute_signing_root(message, domain), signed_exit.signature)
