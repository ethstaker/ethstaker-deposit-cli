import json
import os

import click
from click.testing import CliRunner

from ethstaker_deposit.settings import HoodiSetting, MainnetSetting
from ethstaker_deposit.utils import config
from ethstaker_deposit.utils.click import chain_arguments_decorator, jit_option


CHAIN_SOURCE_FILE = os.path.join(
    os.path.dirname(__file__),
    '..', '..', 'ethstaker_deposit', 'cli', 'generate_keys.py',
)


def make_chain_command():
    @click.command()
    @chain_arguments_decorator('generate_keys_arguments_decorator', CHAIN_SOURCE_FILE)
    @click.pass_context
    def command(ctx: click.Context, chain_setting, **kwargs) -> None:
        click.echo(chain_setting.NETWORK_NAME)

    return command


def make_amount_command():
    @click.command()
    @chain_arguments_decorator('generate_keys_arguments_decorator', CHAIN_SOURCE_FILE)
    @jit_option(default='32', param_decls='--amount', prompt=False)
    @click.pass_context
    def command(ctx: click.Context, chain_setting, amount, **kwargs) -> None:
        click.echo(str(amount))

    return command


def make_unconfigured_amount_command():
    @click.command()
    @jit_option(default='32', param_decls='--amount', prompt=False)
    @click.pass_context
    def command(ctx: click.Context, amount, **kwargs) -> None:
        click.echo(str(amount))

    return command


def test_named_chain_is_normalized_to_chain_setting() -> None:
    result = CliRunner().invoke(make_chain_command(), ['--chain', 'hoodi'])

    assert result.exit_code == 0
    assert result.output.strip() == 'hoodi'


def test_default_chain_is_normalized_to_mainnet_setting(monkeypatch) -> None:
    monkeypatch.setattr(config, 'non_interactive', True)
    result = CliRunner().invoke(make_chain_command(), [], input='\n')

    assert result.exit_code == 0
    assert result.output.splitlines()[-1] == MainnetSetting.NETWORK_NAME


def test_custom_chain_takes_precedence_without_prompt() -> None:
    custom_chain = {
        'network_name': 'custom',
        'genesis_fork_version': '20000910',
        'exit_fork_version': '04017000',
        'genesis_validator_root': '212f13fc4df078b6cb7db228f1c8307566dcecf900867401a92023d7ba99cb5f',
    }

    result = CliRunner().invoke(
        make_chain_command(),
        ['--chain', 'hoodi', '--devnet_chain_setting', json.dumps(custom_chain)],
    )

    assert result.exit_code == 0
    assert result.output.splitlines()[-1] == 'custom'
    assert 'Please choose' not in result.output


def test_chain_is_prompted_when_omitted(monkeypatch) -> None:
    monkeypatch.setattr(config, 'non_interactive', False)
    result = CliRunner().invoke(make_chain_command(), input='hoodi\n')

    assert result.exit_code == 0
    assert result.output.splitlines()[-1] == 'hoodi'


def test_invalid_custom_chain_fails_before_command_execution() -> None:
    result = CliRunner().invoke(make_chain_command(), ['--devnet_chain_setting', 'not-json'])

    assert result.exit_code != 0
    assert result.exception is not None
    assert isinstance(result.exception, Exception)


def test_named_chain_setting_matches_builtin_setting() -> None:
    result = CliRunner().invoke(make_chain_command(), ['--chain', 'hoodi'])

    assert result.exit_code == 0
    assert result.output.strip() == HoodiSetting.NETWORK_NAME


def test_amount_default_uses_named_chain_setting() -> None:
    result = CliRunner().invoke(make_amount_command(), ['--chain', 'hoodi'])

    assert result.exit_code == 0
    assert result.output.strip() == str(HoodiSetting.MIN_ACTIVATION_AMOUNT)


def test_amount_default_uses_custom_devnet_chain_setting() -> None:
    custom_chain = {
        'network_name': 'custom',
        'genesis_fork_version': '20000910',
        'exit_fork_version': '04017000',
        'genesis_validator_root': '212f13fc4df078b6cb7db228f1c8307566dcecf900867401a92023d7ba99cb5f',
        'min_activation_amount': 1,
    }

    result = CliRunner().invoke(
        make_amount_command(),
        ['--devnet_chain_setting', json.dumps(custom_chain)],
    )

    assert result.exit_code == 0
    assert result.output.splitlines()[-1] == '1'


def test_amount_default_falls_back_to_mainnet_without_chain_setting() -> None:
    result = CliRunner().invoke(make_unconfigured_amount_command(), [])

    assert result.exit_code == 0
    assert result.output.strip() == str(MainnetSetting.MIN_ACTIVATION_AMOUNT)
