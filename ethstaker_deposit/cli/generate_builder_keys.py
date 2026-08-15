import click
import os
import time
from typing import Any
from collections.abc import Callable

from eth_typing import HexAddress
from ethstaker_deposit.credentials import (
    CredentialList,
)
from ethstaker_deposit.exceptions import ValidationError
from ethstaker_deposit.utils import config
from ethstaker_deposit.utils.validation import (
    verify_builder_deposit_data_json,
    validate_int_range,
    validate_password_strength,
    validate_withdrawal_address,
    validate_builder_deposit_amount,
    validate_devnet_chain_setting,
)
from ethstaker_deposit.utils.constants import (
    DEFAULT_BUILDER_KEYS_FOLDER_NAME,
)
from ethstaker_deposit.utils.ascii_art import RHINO_0
from ethstaker_deposit.utils.click import (
    captive_prompt_callback,
    choice_prompt_func,
    jit_option,
    prompt_if_none,
    prompt_if_other_is_none,
)
from ethstaker_deposit.utils.intl import (
    closest_match,
    load_text,
)
from ethstaker_deposit.utils.terminal import clear_terminal
from ethstaker_deposit.settings import (
    MAINNET,
    ALL_CHAIN_KEYS,
    get_chain_setting,
    BaseChainSetting,
)


def generate_builder_keys_arguments_decorator(function: Callable[..., Any]) -> Callable[..., Any]:
    '''
    This is a decorator that, when applied to a parent-command, implements the
    to obtain the necessary arguments for the generate_builder_keys() subcommand.
    '''
    decorators = [
        jit_option(
            callback=captive_prompt_callback(
                lambda num, _: validate_int_range(num, 1, 2**32),
                lambda: load_text(['num_builders', 'prompt'], func='generate_builder_keys_arguments_decorator')
            ),
            help=lambda: load_text(['num_builders', 'help'], func='generate_builder_keys_arguments_decorator'),
            param_decls="--num_builders",
            prompt=lambda: load_text(['num_builders', 'prompt'], func='generate_builder_keys_arguments_decorator'),
        ),
        jit_option(
            default=os.getcwd(),
            help=lambda: load_text(['folder', 'help'], func='generate_builder_keys_arguments_decorator'),
            param_decls='--folder',
            type=click.Path(exists=True, file_okay=False, dir_okay=True),
        ),
        jit_option(
            callback=captive_prompt_callback(
                lambda x, _: closest_match(x, ALL_CHAIN_KEYS),
                choice_prompt_func(
                    lambda: load_text(['chain', 'prompt'], func='generate_builder_keys_arguments_decorator'),
                    ALL_CHAIN_KEYS
                ),
                prompt_if=prompt_if_other_is_none('devnet_chain_setting'),
                default=MAINNET,
            ),
            default=MAINNET,
            help=lambda: load_text(['chain', 'help'], func='generate_builder_keys_arguments_decorator'),
            param_decls='--chain',
            prompt=False,  # the callback handles the prompt
        ),
        jit_option(
            callback=captive_prompt_callback(
                lambda password, _: validate_password_strength(password),
                lambda: load_text(['keystore_password', 'prompt'], func='generate_builder_keys_arguments_decorator'),
                lambda: load_text(['keystore_password', 'confirm'], func='generate_builder_keys_arguments_decorator'),
                lambda: load_text(['keystore_password', 'mismatch'], func='generate_builder_keys_arguments_decorator'),
                True,
                prompt_if=prompt_if_none,
            ),
            help=lambda: load_text(['keystore_password', 'help'], func='generate_builder_keys_arguments_decorator'),
            hide_input=True,
            param_decls='--keystore_password',
            prompt=False,  # the callback handles the prompt
        ),
        jit_option(
            callback=captive_prompt_callback(
                lambda address, _: validate_withdrawal_address(None, None, address, require=True),
                lambda: load_text(['arg_execution_address', 'prompt'],
                                  func='generate_builder_keys_arguments_decorator'),
                lambda: load_text(['arg_execution_address', 'confirm'],
                                  func='generate_builder_keys_arguments_decorator'),
                lambda: load_text(['arg_execution_address', 'mismatch'],
                                  func='generate_builder_keys_arguments_decorator'),
                prompt_if=prompt_if_none,
            ),
            help=lambda: load_text(['arg_execution_address', 'help'], func='generate_builder_keys_arguments_decorator'),
            param_decls=['--execution_address'],
            prompt=False,  # the callback handles the prompt
        ),
        jit_option(
            callback=captive_prompt_callback(
                lambda builder_amount, _: validate_builder_deposit_amount(builder_amount),
                lambda: load_text(['arg_builder_amount', 'prompt'], func='generate_builder_keys_arguments_decorator'),
                prompt_if=prompt_if_none,
                default='1',
            ),
            default='1',
            help=lambda: load_text(['arg_builder_amount', 'help'], func='generate_builder_keys_arguments_decorator'),
            param_decls='--builder_amount',
            prompt=False,  # the callback handles the prompt
            show_default=True,
        ),
        jit_option(
            default=False,
            is_flag=True,
            param_decls='--pbkdf2',
            help=lambda: load_text(['arg_pbkdf2', 'help'], func='generate_builder_keys_arguments_decorator'),
        ),
        jit_option(
            callback=validate_devnet_chain_setting,
            default=None,
            help=lambda: load_text(['arg_devnet_chain_setting', 'help'],
                                   func='generate_builder_keys_arguments_decorator'),
            param_decls='--devnet_chain_setting',
            is_eager=True,
        ),
    ]
    for decorator in reversed(decorators):
        function = decorator(function)
    return function


@click.command()
@click.pass_context
def generate_builder_keys(ctx: click.Context, builder_start_index: int,
                          num_builders: int, folder: str, chain: str, keystore_password: str,
                          execution_address: HexAddress, builder_amount: float, pbkdf2: bool,
                          devnet_chain_setting: BaseChainSetting | None, **kwargs: Any) -> None:
    mnemonic = ctx.obj['mnemonic']
    mnemonic_password = ctx.obj['mnemonic_password']

    # Get chain setting
    chain_setting = devnet_chain_setting if devnet_chain_setting is not None else get_chain_setting(chain)

    # `builder_amount` is already gwei-denominated by validate_builder_deposit_amount
    # No chain multiplier is used here as implementations by other chains is unknown
    amounts = [builder_amount] * num_builders
    folder = os.path.join(folder, DEFAULT_BUILDER_KEYS_FOLDER_NAME)

    if not os.path.exists(folder):
        os.mkdir(folder)
    clear_terminal()
    click.echo(RHINO_0)
    click.echo(load_text(['msg_key_creation']))
    credentials = CredentialList.from_mnemonic(
        mnemonic=mnemonic,
        mnemonic_password=mnemonic_password,
        num_keys=num_builders,
        amounts=amounts,
        chain_setting=chain_setting,
        start_index=builder_start_index,
        hex_withdrawal_address=execution_address,
        use_pbkdf2=pbkdf2,
        is_builder=True,
    )

    timestamp = time.time()

    keystore_filefolders = credentials.export_keystores(password=keystore_password, folder=folder, timestamp=timestamp)
    deposits_file = credentials.export_builder_deposit_data_json(folder=folder, timestamp=timestamp)
    if not credentials.verify_keystores(keystore_filefolders=keystore_filefolders, password=keystore_password):
        raise ValidationError(load_text(['err_verify_keystores']))
    if not verify_builder_deposit_data_json(deposits_file, credentials.credentials):
        raise ValidationError(load_text(['err_verify_deposit']))
    click.echo(load_text(['msg_creation_success']) + folder)
    if not config.non_interactive:
        click.pause(load_text(['msg_pause']))
