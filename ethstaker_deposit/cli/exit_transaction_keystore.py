import click
import os
import sys
import time
from typing import Any

from ethstaker_deposit.exceptions import ValidationError
from ethstaker_deposit.utils.exit_transaction import exit_transaction_generation, export_exit_transaction_json
from ethstaker_deposit.key_handling.keystore import Keystore
from ethstaker_deposit.settings import (
    BaseChainSetting,
)
from ethstaker_deposit.utils import config
from ethstaker_deposit.utils.click import (
    chain_arguments_decorator,
    captive_prompt_callback,
    jit_option,
    prompt_if_none,
)
from ethstaker_deposit.utils.constants import DEFAULT_EXIT_TRANSACTION_FOLDER_NAME
from ethstaker_deposit.utils.symlink import warn_if_output_directory_symlink
from ethstaker_deposit.utils.intl import load_text
from ethstaker_deposit.utils.validation import (
    validate_int_range,
    validate_keystore_file,
    verify_signed_exit_json,
    validate_genesis_validators_root,
)


FUNC_NAME = 'exit_transaction_keystore'


@click.command(
    help=load_text(['arg_exit_transaction_keystore', 'help'], func=FUNC_NAME),
)
@chain_arguments_decorator(FUNC_NAME, __file__, 'arg_exit_transaction_keystore_chain')
@jit_option(
    callback=captive_prompt_callback(
        lambda file, _: validate_keystore_file(file),
        lambda: load_text(['arg_exit_transaction_keystore_keystore', 'prompt'], func=FUNC_NAME),
        prompt_if=prompt_if_none,
    ),
    help=lambda: load_text(['arg_exit_transaction_keystore_keystore', 'help'], func=FUNC_NAME),
    param_decls='--keystore',
    prompt=False,
)
@jit_option(
    callback=captive_prompt_callback(
        lambda x, _: x,
        lambda: load_text(['arg_exit_transaction_keystore_keystore_password', 'prompt'], func=FUNC_NAME),
        None,
        lambda: load_text(['arg_exit_transaction_keystore_keystore_password', 'invalid'], func=FUNC_NAME),
        True,
    ),
    help=lambda: load_text(['arg_exit_transaction_keystore_keystore_password', 'help'], func=FUNC_NAME),
    hide_input=True,
    param_decls='--keystore_password',
    prompt=lambda: load_text(['arg_exit_transaction_keystore_keystore_password', 'prompt'], func=FUNC_NAME),
)
@jit_option(
    callback=captive_prompt_callback(
        lambda num, _: validate_int_range(num, 0, 2**32),
        lambda: load_text(['arg_validator_index', 'prompt'], func=FUNC_NAME),
    ),
    help=lambda: load_text(['arg_validator_index', 'help'], func=FUNC_NAME),
    param_decls='--validator_index',
    prompt=lambda: load_text(['arg_validator_index', 'prompt'], func=FUNC_NAME),
)
@jit_option(
    default=0,
    help=lambda: load_text(['arg_exit_transaction_keystore_epoch', 'help'], func=FUNC_NAME),
    param_decls='--epoch',
)
@jit_option(
    default=os.getcwd(),
    help=lambda: load_text(['arg_exit_transaction_keystore_output_folder', 'help'], func=FUNC_NAME),
    param_decls='--output_folder',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.pass_context
def exit_transaction_keystore(
        ctx: click.Context,
        chain_setting: BaseChainSetting,
        keystore: Keystore,
        keystore_password: str,
        validator_index: int,
        epoch: int,
        output_folder: str,
        **kwargs: Any) -> None:
    folder = os.path.join(output_folder, DEFAULT_EXIT_TRANSACTION_FOLDER_NAME)
    warn_if_output_directory_symlink(folder)

    try:
        secret_bytes = keystore.decrypt(keystore_password)
    except ValueError:
        click.echo(load_text(['arg_exit_transaction_keystore_keystore_password', 'mismatch']), err=True)
        sys.exit(1)

    signing_key = int.from_bytes(secret_bytes, 'big')

    validate_genesis_validators_root(chain_setting)

    signed_exit = exit_transaction_generation(
        chain_setting=chain_setting,
        signing_key=signing_key,
        validator_index=validator_index,
        epoch=epoch,
    )

    if not os.path.exists(folder):
        os.mkdir(folder)

    click.echo(load_text(['msg_exit_transaction_creation']))
    saved_folder = export_exit_transaction_json(folder=folder, signed_exit=signed_exit, timestamp=time.time())

    click.echo(load_text(['msg_verify_exit_transaction']))
    if (not verify_signed_exit_json(saved_folder, keystore.pubkey, chain_setting)):
        raise ValidationError(load_text(['err_verify_exit_transaction']))

    click.echo(load_text(['msg_creation_success']) + saved_folder)
    if not config.non_interactive:
        click.pause(load_text(['msg_pause']))
