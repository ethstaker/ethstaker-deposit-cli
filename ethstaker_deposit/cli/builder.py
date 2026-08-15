import click
import pyperclip
from typing import Any

from ethstaker_deposit.key_handling.key_derivation.mnemonic import (
    get_mnemonic,
    reconstruct_mnemonic,
)
from ethstaker_deposit.cli.existing_mnemonic import (
    validate_mnemonic,
)
from ethstaker_deposit.exceptions import ValidationError
from ethstaker_deposit.utils import config
from ethstaker_deposit.utils.click import (
    captive_prompt_callback,
    choice_prompt_func,
    jit_option,
    prompt_if_none,
    prompt_if_other_is_none,
)
from ethstaker_deposit.utils.constants import (
    MNEMONIC_LANG_OPTIONS,
    WORD_LISTS_PATH,
)
from ethstaker_deposit.utils.intl import (
    fuzzy_reverse_dict_lookup,
    load_text,
    get_first_options,
)
from ethstaker_deposit.utils.terminal import clear_terminal
from ethstaker_deposit.utils.validation import validate_int_range

from .generate_builder_keys import (
    generate_builder_keys,
    generate_builder_keys_arguments_decorator,
)

languages = get_first_options(MNEMONIC_LANG_OPTIONS)


def _mnemonic_language_default() -> str | None:
    # If an existing mnemonic was supplied, its language is auto-detected by validate_mnemonic.
    # A fresh mnemonic needs a wordlist language chosen up-front
    ctx = click.get_current_context(silent=True)
    if ctx is not None and ctx.params.get('mnemonic'):
        return None
    return load_text(['arg_mnemonic_language', 'default'], func='builder')


def _process_mnemonic_language(mnemonic_language: str, _: Any) -> str | None:
    return fuzzy_reverse_dict_lookup(mnemonic_language, MNEMONIC_LANG_OPTIONS) if mnemonic_language else None


def _resolve_mnemonic(ctx: click.Context, param: Any, mnemonic: str) -> str | None:
    if mnemonic:
        # Provided directly via --mnemonic
        return validate_mnemonic(mnemonic=mnemonic, language=ctx.params.get('mnemonic_language'))
    if config.non_interactive:
        return None
    has_existing = click.confirm(load_text(['arg_mnemonic', 'existing_confirm'], func='builder'), default=False)
    if not has_existing:
        return None
    return captive_prompt_callback(
        lambda mnemonic, _: validate_mnemonic(mnemonic=mnemonic, language=ctx.params.get('mnemonic_language')),
        lambda: load_text(['arg_mnemonic', 'prompt'], func='builder'),
        prompt_if=prompt_if_none,
    )(ctx, param, mnemonic)


def _resolve_mnemonic_password(ctx: click.Context, param: Any, mnemonic_password: str) -> str:
    resolved = captive_prompt_callback(
        lambda x, _: x,
        lambda: load_text(['arg_mnemonic_password', 'prompt'], func='builder'),
        lambda: load_text(['arg_mnemonic_password', 'confirm'], func='builder'),
        lambda: load_text(['arg_mnemonic_password', 'mismatch'], func='builder'),
        hide_input=True,
    )(ctx, param, mnemonic_password)
    if resolved and not ctx.params.get('mnemonic'):
        # Do not allow mnemonic password if mnemonic is not provided
        raise ValidationError(load_text(['err_mnemonic_password_not_allowed'], func='builder'))
    return resolved


@click.command(
    help=load_text(['arg_builder', 'help'], func='builder'),
)
@click.pass_context
@jit_option(
    callback=_resolve_mnemonic,
    help=lambda: load_text(['arg_mnemonic', 'help'], func='builder'),
    param_decls='--mnemonic',
    default=None,
    prompt=False,
    type=str,
    is_eager=True,
)
@jit_option(
    callback=_resolve_mnemonic_password,
    default='',
    help=lambda: load_text(['arg_mnemonic_password', 'help'], func='builder'),
    hidden=True,
    param_decls='--mnemonic_password',
    prompt=False,
)
@jit_option(
    callback=captive_prompt_callback(
        _process_mnemonic_language,
        choice_prompt_func(lambda: load_text(['arg_mnemonic_language', 'prompt'], func='builder'), languages),
        default=_mnemonic_language_default,
        prompt_if=prompt_if_other_is_none('mnemonic'),
    ),
    default=_mnemonic_language_default,
    help=lambda: load_text(['arg_mnemonic_language', 'help'], func='builder'),
    param_decls='--mnemonic_language',
    prompt=False,
)
@jit_option(
    # We do not want to request a start index if a mnemonic is not provided as it
    # is assumed to be 0, unless provided. If a mnemonic is provided we must request
    # the start index if not already provided
    callback=lambda ctx, param, num: (
        captive_prompt_callback(
            lambda num, _: validate_int_range(num, 0, 2**32),
            lambda: load_text(['arg_builder_start_index', 'prompt'], func='builder'),
            lambda: load_text(['arg_builder_start_index', 'confirm'], func='builder'),
            prompt_if=prompt_if_none,
        )(ctx, param, num)
        if ctx.params.get('mnemonic')
        else captive_prompt_callback(
            lambda num, _: validate_int_range(num, 0, 2**32),
            lambda: load_text(['arg_builder_start_index', 'prompt'], func='builder'),
        )(ctx, param, num)
    ),
    default=0,
    help=lambda: load_text(['arg_builder_start_index', 'help'], func='builder'),
    param_decls="--builder_start_index",
    prompt=False,
)
@generate_builder_keys_arguments_decorator
def builder(ctx: click.Context, mnemonic: str, mnemonic_password: str, mnemonic_language: str, **kwargs: Any) -> None:
    if not mnemonic:
        mnemonic = get_mnemonic(language=mnemonic_language, words_path=WORD_LISTS_PATH)
        test_mnemonic = ''
        while mnemonic != reconstruct_mnemonic(test_mnemonic, WORD_LISTS_PATH, mnemonic_language):
            clear_terminal()
            click.echo(
                load_text(['msg_mnemonic_presentation'], func='builder')
                + '\n\n********************\n'
                + load_text(['msg_mnemonic_clipboard_warning'], func='builder')
                + '\n********************'
            )
            click.echo(f'\n\n{mnemonic}\n\n')
            click.pause(load_text(['msg_press_any_key'], func='builder'))

            clear_terminal()
            test_mnemonic = click.prompt(
                load_text(['msg_mnemonic_retype_prompt'], func='builder')
                + '\n\n********************\n'
                + load_text(['msg_mnemonic_clipboard_warning'], func='builder')
                + '\n********************\n\n'
            )
        clear_terminal()
        # Clear clipboard
        try:  # Failing this on headless Linux is expected
            click.pause(load_text(['msg_confirm_clipboard_clearing'], func='builder'))
            pyperclip.copy(' ')
        except Exception:  # noqa: S110
            pass

    ctx.obj = {'mnemonic': mnemonic, 'mnemonic_password': mnemonic_password}
    ctx.forward(generate_builder_keys)
