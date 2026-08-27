from tests.test_integration.helpers import build_shell_command


def test_build_shell_command_does_not_quote_command() -> None:
    # The leading executable invocation must never be quoted, even when it
    # contains a space (Windows: 'bash deposit.sh').
    assert build_shell_command('bash deposit.sh', '--language', 'english') == \
        'bash deposit.sh --language english'


def test_build_shell_command_quotes_values_with_spaces() -> None:
    assert build_shell_command('./deposit.sh', '--mnemonic', 'aban aban aban') == \
        './deposit.sh --mnemonic "aban aban aban"'


def test_build_shell_command_leaves_simple_args_alone() -> None:
    assert build_shell_command('./deposit.sh', '--chain', 'mainnet', '--num_validators', '1') == \
        './deposit.sh --chain mainnet --num_validators 1'


def test_build_shell_command_empty() -> None:
    assert build_shell_command() == ''
