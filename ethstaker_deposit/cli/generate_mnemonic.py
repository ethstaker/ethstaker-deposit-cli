import sys
import click

from typing import (
    Any,
)

from ethstaker_deposit.key_handling.key_derivation.mnemonic import (
    get_mnemonic,
)
from ethstaker_deposit.utils import config
from ethstaker_deposit.utils.click import (
    captive_prompt_callback,
    choice_prompt_func,
    jit_option,
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
from ethstaker_deposit.utils.file_handling import (
    sensitive_opener,
)


languages = get_first_options(MNEMONIC_LANG_OPTIONS)


@click.command(
    help=load_text(['arg_generate_mnemonic', 'help'], func='generate_mnemonic'),
)
@click.pass_context
@jit_option(
    '--mnemonic_language',
    callback=captive_prompt_callback(
        lambda mnemonic_language, _: fuzzy_reverse_dict_lookup(mnemonic_language, MNEMONIC_LANG_OPTIONS),
        choice_prompt_func(lambda: load_text(['arg_mnemonic_language', 'prompt'], func='generate_mnemonic'), languages),
        default=lambda: load_text(['arg_mnemonic_language', 'default'], func='generate_mnemonic'),
    ),
    default=lambda: load_text(['arg_mnemonic_language', 'default'], func='generate_mnemonic'),
    help=lambda: load_text(['arg_mnemonic_language', 'help'], func='generate_mnemonic'),
    prompt=choice_prompt_func(
        lambda: load_text(['arg_mnemonic_language', 'prompt'], func='generate_mnemonic'), languages),
    type=str,
)
@jit_option(
    '--output_file',
    help=lambda: load_text(['arg_output_file', 'help'], func='generate_mnemonic'),
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, resolve_path=True)
)
def generate_mnemonic(ctx: click.Context, mnemonic_language: str, **kwargs: Any) -> None:
    mnemonic = get_mnemonic(language=mnemonic_language, words_path=WORD_LISTS_PATH)

    filepath = ctx.params.get('output_file', None)
    if filepath is not None:
        # We are writing the mnemonic in a file
        try:
            with open(filepath, 'w', encoding='utf-8', opener=sensitive_opener) as f:
                f.write(mnemonic)
            if not config.non_interactive:
                click.echo('\n%s %s\n' % (load_text(['msg_mnemonic_file_written']), filepath))
        except FileNotFoundError as e:
            click.echo("\n%s\n%s\n" % (
                load_text(['arg_output_file', 'err_not_found'], func='generate_mnemonic'),
                str(e)), err=True)
            sys.exit(1)
        except PermissionError as e:
            click.echo("\n%s\n%s\n" % (
                load_text(['arg_output_file', 'err_perm_denied'], func='generate_mnemonic'),
                str(e)), err=True)
            sys.exit(1)
        except IsADirectoryError as e:
            click.echo("\n%s\n%s\n" % (
                load_text(['arg_output_file', 'err_directory_not_file'], func='generate_mnemonic'),
                str(e)), err=True)
            sys.exit(1)
        except OSError as e:
            click.echo("\n%s\n%s\n" % (
                load_text(['arg_output_file', 'err_os',], func='generate_mnemonic'),
                str(e)), err=True)
            sys.exit(1)
        except Exception as e:
            click.echo("\n%s\n%s\n" % (
                load_text(['arg_output_file', 'err_exception'], func='generate_mnemonic'),
                str(e)), err=True)
            sys.exit(1)

    else:
        # We are displaying the mnemonic on screen
        if not config.non_interactive:
            click.echo('\n%s\n' % load_text(['msg_mnemonic_presentation']))
        click.echo(mnemonic)

    if not config.non_interactive:
        click.echo('\n%s' % load_text(['msg_mnemonic_next']))
