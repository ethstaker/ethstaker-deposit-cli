import json
import click
import os
import sys
import time

from eth_typing import HexAddress
from eth_utils import to_canonical_address
from py_ecc.bls import G2ProofOfPossession as bls
from typing import Any

from ethstaker_deposit.cli.generate_keys import get_default_amount, get_amount_prompt_from_template
from ethstaker_deposit.key_handling.keystore import Keystore
from ethstaker_deposit.settings import (
    DEPOSIT_CLI_VERSION,
    BaseChainSetting,
)
from ethstaker_deposit.utils import config
from ethstaker_deposit.utils.click import (
    chain_arguments_decorator,
    captive_prompt_callback,
    jit_option,
    prompt_if_none,
    prompt_if_other_exists,
    regular_withdrawal_alias,
)
from ethstaker_deposit.utils.constants import (
    DEFAULT_PARTIAL_DEPOSIT_FOLDER_NAME,
    EXECUTION_ADDRESS_WITHDRAWAL_PREFIX,
    COMPOUNDING_WITHDRAWAL_PREFIX,
)
from ethstaker_deposit.utils.export_data import export_deposit_data_json
from ethstaker_deposit.utils.symlink import warn_if_output_directory_symlink
from ethstaker_deposit.utils.intl import load_text
from ethstaker_deposit.utils.ssz import (
    DepositData,
    DepositMessage,
    compute_deposit_domain,
    compute_signing_root,
)
from ethstaker_deposit.utils.validation import (
    validate_deposit,
    validate_keystore_file,
    validate_deposit_amount,
    validate_withdrawal_address,
    validate_yesno,
)


FUNC_NAME = 'partial_deposit'


@click.command(
    help=load_text(['arg_partial_deposit', 'help'], func=FUNC_NAME),
)
@chain_arguments_decorator(FUNC_NAME, __file__, 'arg_partial_deposit_chain')
@jit_option(
    callback=captive_prompt_callback(
        lambda file, _: validate_keystore_file(file),
        lambda: load_text(['arg_partial_deposit_keystore', 'prompt'], func=FUNC_NAME),
        prompt_if=prompt_if_none,
    ),
    help=lambda: load_text(['arg_partial_deposit_keystore', 'help'], func=FUNC_NAME),
    param_decls='--keystore',
    prompt=False,
)
@jit_option(
    callback=captive_prompt_callback(
        lambda x, _: x,
        lambda: load_text(['arg_partial_deposit_keystore_password', 'prompt'], func=FUNC_NAME),
        None,
        lambda: load_text(['arg_partial_deposit_keystore_password', 'invalid'], func=FUNC_NAME),
        True,
    ),
    help=lambda: load_text(['arg_partial_deposit_keystore_password', 'help'], func=FUNC_NAME),
    hide_input=True,
    param_decls='--keystore_password',
    prompt=lambda: load_text(['arg_partial_deposit_keystore_password', 'prompt'], func=FUNC_NAME),
)
@jit_option(
    callback=captive_prompt_callback(
        lambda amount, **kwargs: validate_deposit_amount(amount, **kwargs),
        get_amount_prompt_from_template,
        default=get_default_amount,
        prompt_if=prompt_if_none,
        prompt_marker="amount",
    ),
    help=lambda: load_text(['arg_partial_deposit_amount', 'help'], func=FUNC_NAME),
    param_decls='--amount',
    prompt=False,  # the callback handles the prompt, to avoid second callback with gwei
    show_default=True,
)
@jit_option(
    callback=captive_prompt_callback(
        lambda address, _: validate_withdrawal_address(None, None, address, True),
        lambda: load_text(['arg_withdrawal_address', 'prompt'], func=FUNC_NAME),
        lambda: load_text(['arg_withdrawal_address', 'confirm'], func=FUNC_NAME),
        lambda: load_text(['arg_withdrawal_address', 'mismatch'], func=FUNC_NAME),
        prompt_if=prompt_if_none,
    ),
    help=lambda: load_text(['arg_withdrawal_address', 'help'], func=FUNC_NAME),
    param_decls=['--withdrawal_address', '--execution_address', '--eth1_withdrawal_credentials'],
    prompt=False,  # the callback handles the prompt
)
@jit_option(
    callback=captive_prompt_callback(
        lambda value, _: validate_yesno(None, None, value),
        lambda: load_text(['arg_compounding', 'prompt'], func=FUNC_NAME),
        default="True",
        prompt_if=prompt_if_other_exists('withdrawal_address'),
    ),
    default=True,
    help=lambda: load_text(['arg_compounding', 'help'], func=FUNC_NAME),
    param_decls='--compounding/--regular_withdrawal',
    prompt=False,  # the callback handles the prompt
    type=bool,
    show_default=True,
)
@jit_option(
    callback=regular_withdrawal_alias,
    default=None,
    help='',
    hidden=True,
    is_flag=True,
    flag_value=False,
    param_decls='--regular-withdrawal',
)
@jit_option(
    default=os.getcwd(),
    help=lambda: load_text(['arg_partial_deposit_output_folder', 'help'], func=FUNC_NAME),
    param_decls='--output_folder',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.pass_context
def partial_deposit(
        ctx: click.Context,
        chain_setting: BaseChainSetting,
        keystore: Keystore,
        keystore_password: str,
        amount: int,
        withdrawal_address: HexAddress,
        compounding: bool,
        output_folder: str,
        **kwargs: Any) -> None:
    folder = os.path.join(output_folder, DEFAULT_PARTIAL_DEPOSIT_FOLDER_NAME)
    warn_if_output_directory_symlink(folder)

    try:
        secret_bytes = keystore.decrypt(keystore_password)
    except ValueError:
        click.echo(load_text(['arg_partial_deposit_keystore_password', 'mismatch']), err=True)
        sys.exit(1)

    signing_key = int.from_bytes(secret_bytes, 'big')

    if compounding:
        withdrawal_credentials = COMPOUNDING_WITHDRAWAL_PREFIX
    else:
        withdrawal_credentials = EXECUTION_ADDRESS_WITHDRAWAL_PREFIX

    amount = amount * chain_setting.MULTIPLIER

    withdrawal_credentials += b'\x00' * 11
    withdrawal_credentials += to_canonical_address(withdrawal_address)

    deposit_message = DepositMessage(  # type: ignore[no-untyped-call]
        pubkey=bls.SkToPk(signing_key),
        withdrawal_credentials=withdrawal_credentials,
        amount=amount
    )

    domain = compute_deposit_domain(fork_version=chain_setting.GENESIS_FORK_VERSION)

    signing_root = compute_signing_root(deposit_message, domain)
    signature = bls.Sign(signing_key, signing_root)

    signed_deposit = DepositData(  # type: ignore[no-untyped-call]
        **deposit_message.as_dict(),  # type: ignore[no-untyped-call]
        signature=signature
    )

    if not os.path.exists(folder):
        os.mkdir(folder)

    click.echo(load_text(['msg_partial_deposit_creation']))
    deposit_data = signed_deposit.as_dict()  # type: ignore[no-untyped-call]
    deposit_data.update({'deposit_message_root': deposit_message.hash_tree_root})
    deposit_data.update({'deposit_data_root': signed_deposit.hash_tree_root})
    deposit_data.update({'fork_version': chain_setting.GENESIS_FORK_VERSION})
    deposit_data.update({'network_name': chain_setting.NETWORK_NAME})
    deposit_data.update({'deposit_cli_version': DEPOSIT_CLI_VERSION})
    saved_folder = export_deposit_data_json(folder, time.time(), [deposit_data])

    click.echo(load_text(['msg_verify_partial_deposit']))
    deposit_json = []
    with open(saved_folder, encoding='utf-8') as f:
        deposit_json = json.load(f)

    if (not validate_deposit(deposit_json[0], chain_setting)):
        click.echo(load_text(['err_verify_partial_deposit']))
        return

    click.echo(load_text(['msg_creation_success']) + saved_folder)
    if not config.non_interactive:
        click.pause(load_text(['msg_pause']))
