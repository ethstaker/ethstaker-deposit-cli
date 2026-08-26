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
    verify_deposit_data_json,
    validate_int_range,
    validate_password_strength,
    validate_withdrawal_address,
    validate_yesno,
    validate_deposit_amount,
)
from ethstaker_deposit.utils.constants import (
    DEFAULT_VALIDATOR_KEYS_FOLDER_NAME,
    ETH2GWEI
)
from ethstaker_deposit.utils.ascii_art import RHINO_0
from ethstaker_deposit.utils.click import (
    chain_arguments_decorator_list,
    captive_prompt_callback,
    jit_option,
    prompt_if_none,
    prompt_if_other_exists,
    prompt_if_other_value,
    regular_withdrawal_alias,
)
from ethstaker_deposit.utils.intl import (
    load_text,
)
from ethstaker_deposit.utils.terminal import clear_terminal
from ethstaker_deposit.utils.symlink import warn_if_output_directory_symlink
from ethstaker_deposit.settings import (
    MainnetSetting,
    BaseChainSetting,
)


def generate_keys_arguments_decorator(function: Callable[..., Any]) -> Callable[..., Any]:
    '''
    This is a decorator that, when applied to a parent-command, implements the
    to obtain the necessary arguments for the generate_keys() subcommand.
    '''
    decorators = [
        jit_option(
            callback=captive_prompt_callback(
                lambda num, _: validate_int_range(num, 1, 2**32),
                lambda: load_text(['num_validators', 'prompt'], func='generate_keys_arguments_decorator')
            ),
            help=lambda: load_text(['num_validators', 'help'], func='generate_keys_arguments_decorator'),
            param_decls="--num_validators",
            prompt=lambda: load_text(['num_validators', 'prompt'], func='generate_keys_arguments_decorator'),
        ),
        jit_option(
            default=os.getcwd(),
            help=lambda: load_text(['folder', 'help'], func='generate_keys_arguments_decorator'),
            param_decls='--folder',
            type=click.Path(exists=True, file_okay=False, dir_okay=True),
        ),
        *chain_arguments_decorator_list(file_path=__file__),
        jit_option(
            callback=captive_prompt_callback(
                lambda password, _: validate_password_strength(password),
                lambda: load_text(['keystore_password', 'prompt'], func='generate_keys_arguments_decorator'),
                lambda: load_text(['keystore_password', 'confirm'], func='generate_keys_arguments_decorator'),
                lambda: load_text(['keystore_password', 'mismatch'], func='generate_keys_arguments_decorator'),
                True,
                prompt_if=prompt_if_none,
            ),
            help=lambda: load_text(['keystore_password', 'help'], func='generate_keys_arguments_decorator'),
            hide_input=True,
            param_decls='--keystore_password',
            prompt=False,  # the callback handles the prompt
        ),
        jit_option(
            callback=captive_prompt_callback(
                lambda address, _: validate_withdrawal_address(None, None, address, True),
                lambda: load_text(['arg_withdrawal_address', 'prompt'], func='generate_keys_arguments_decorator'),
                lambda: load_text(['arg_withdrawal_address', 'confirm'], func='generate_keys_arguments_decorator'),
                lambda: load_text(['arg_withdrawal_address', 'mismatch'], func='generate_keys_arguments_decorator'),
                prompt_if=prompt_if_none,
            ),
            help=lambda: load_text(['arg_withdrawal_address', 'help'], func='generate_keys_arguments_decorator'),
            param_decls=['--withdrawal_address', '--execution_address', '--eth1_withdrawal_address'],
            prompt=False,  # the callback handles the prompt
        ),
        jit_option(
            callback=captive_prompt_callback(
                lambda value, _: validate_yesno(None, None, value),
                lambda: load_text(['arg_compounding', 'prompt'], func='generate_keys_arguments_decorator'),
                default='yes',
                prompt_if=prompt_if_other_exists('withdrawal_address'),
            ),
            default='yes',
            help=lambda: load_text(['arg_compounding', 'help'], func='generate_keys_arguments_decorator'),
            param_decls='--compounding/--regular_withdrawal',
            prompt=False,  # the callback handles the prompt
            type=bool,
            show_default='compounding',
        ),
        jit_option(
            callback=regular_withdrawal_alias,
            default=None,
            help='',
            hidden=True,
            is_flag=True,
            flag_value=False,
            param_decls='--regular-withdrawal',
        ),
        jit_option(
            callback=captive_prompt_callback(
                lambda amount, **kwargs: validate_deposit_amount(amount, **kwargs),
                get_amount_prompt_from_template,
                prompt_if=prompt_if_other_value('compounding', True),
                default=get_default_amount,
                prompt_marker="amount",
            ),
            help=lambda: load_text(['arg_amount', 'help'], func='generate_keys_arguments_decorator'),
            param_decls='--amount',
            prompt=False,  # the callback handles the prompt
            show_default=True,
        ),
        jit_option(
            default=False,
            is_flag=True,
            param_decls='--pbkdf2',
            help=lambda: load_text(['arg_pbkdf2', 'help'], func='generate_keys_arguments_decorator'),
        ),
    ]
    for decorator in reversed(decorators):
        function = decorator(function)
    return function


def get_amount_prompt_from_template() -> str:
    ctx = click.get_current_context(silent=True)
    chain_setting = ctx.params.get('chain_setting') if ctx is not None else None
    if chain_setting is None:
        chain_setting = MainnetSetting
    min_deposit = chain_setting.MIN_DEPOSIT_AMOUNT
    activation_amount = chain_setting.MIN_ACTIVATION_AMOUNT
    template = load_text(['arg_amount', 'prompt'], func='generate_keys_arguments_decorator')
    return template.format(min_deposit=min_deposit, activation_amount=activation_amount)


def get_default_amount() -> str:
    ctx = click.get_current_context(silent=True)
    chain_setting = ctx.params.get('chain_setting') if ctx is not None else None
    if chain_setting is None:
        chain_setting = MainnetSetting
    return str(chain_setting.MIN_ACTIVATION_AMOUNT)


@click.command()
@click.pass_context
def generate_keys(ctx: click.Context, validator_start_index: int,
                  num_validators: int, folder: str, chain_setting: BaseChainSetting, keystore_password: str,
                  withdrawal_address: HexAddress, compounding: bool, amount: float, pbkdf2: bool,
                  **kwargs: Any) -> None:
    mnemonic = ctx.obj['mnemonic']
    mnemonic_password = ctx.obj['mnemonic_password']

    if not compounding:
        amount = chain_setting.MIN_ACTIVATION_AMOUNT * ETH2GWEI
    amounts = [amount] * num_validators
    folder = os.path.join(folder, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    warn_if_output_directory_symlink(folder)

    amounts = [amount * chain_setting.MULTIPLIER for amount in amounts]

    if not os.path.exists(folder):
        os.mkdir(folder)
    clear_terminal()
    click.echo(RHINO_0)
    click.echo(load_text(['msg_key_creation']))
    credentials = CredentialList.from_mnemonic(
        mnemonic=mnemonic,
        mnemonic_password=mnemonic_password,
        num_keys=num_validators,
        amounts=amounts,
        chain_setting=chain_setting,
        start_index=validator_start_index,
        hex_withdrawal_address=withdrawal_address,
        compounding=compounding,
        use_pbkdf2=pbkdf2
    )

    timestamp = time.time()

    keystore_filefolders = credentials.export_keystores(password=keystore_password, folder=folder, timestamp=timestamp)
    deposits_file = credentials.export_deposit_data_json(folder=folder, timestamp=timestamp)
    if not credentials.verify_keystores(keystore_filefolders=keystore_filefolders, password=keystore_password):
        raise ValidationError(load_text(['err_verify_keystores']))
    if not verify_deposit_data_json(deposits_file, credentials.credentials, chain_setting):
        raise ValidationError(load_text(['err_verify_deposit']))
    click.echo(load_text(['msg_creation_success']) + folder)
    if not config.non_interactive:
        click.pause(load_text(['msg_pause']))
