import os
import socket
import sys

import click
import pytest
from click.testing import CliRunner

from ethstaker_deposit.deposit import check_connectivity, cli, run
from tests.test_cli.helpers import clean_key_folder


def test_should_pause_if_connected(monkeypatch) -> None:
    pause_called = False

    def _mock_click_pause(text):
        nonlocal pause_called
        pause_called = True

    def _mock_socket_getaddrinfo(url, port):
        return True

    monkeypatch.setattr(click, 'pause', _mock_click_pause)
    monkeypatch.setattr(socket, 'getaddrinfo', _mock_socket_getaddrinfo)

    check_connectivity()
    assert pause_called is True


def test_should_not_pause_if_not_connected(monkeypatch) -> None:
    pause_called = False

    def _mock_click_pause(text):
        nonlocal pause_called
        pause_called = True

    def _mock_socket_getaddrinfo(url, port):
        raise OSError()

    monkeypatch.setattr(click, 'pause', _mock_click_pause)
    monkeypatch.setattr(socket, 'getaddrinfo', _mock_socket_getaddrinfo)

    check_connectivity()
    assert pause_called is False


def test_should_check_connectivity_by_default(monkeypatch) -> None:
    connectivity_called = False

    def _mock_socket_getaddrinfo(url, port):
        nonlocal connectivity_called
        connectivity_called = True
        raise OSError()

    monkeypatch.setattr(socket, 'getaddrinfo', _mock_socket_getaddrinfo)

    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_key_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)
    runner = CliRunner()
    withdrawal_address = '0x00000000219ab540356cBB839Cbe05303d7705Fa'
    inputs = [
        withdrawal_address,
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '0', '0', '1', 'mainnet', 'MyPasswordIs', 'MyPasswordIs', 'no', '']
    data = '\n'.join(inputs)
    arguments = [
        '--language', 'english',
        'existing-mnemonic',
        '--withdrawal_address', withdrawal_address,
        '--folder', my_folder_path,

    ]
    result = runner.invoke(cli, arguments, input=data)

    assert result.exit_code == 0
    assert connectivity_called is True

    clean_key_folder(my_folder_path)


def test_should_not_check_connectivity_with_ignore_connectivity(monkeypatch) -> None:
    connectivity_called = False

    def _mock_socket_getaddrinfo(url, port):
        nonlocal connectivity_called
        connectivity_called = True
        raise OSError()

    monkeypatch.setattr(socket, 'getaddrinfo', _mock_socket_getaddrinfo)
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_key_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)
    runner = CliRunner()
    withdrawal_address = '0x00000000219ab540356cBB839Cbe05303d7705Fa'
    inputs = [
        withdrawal_address,
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        '0', '0', '1', 'mainnet', 'MyPasswordIs', 'MyPasswordIs', 'no', '']
    data = '\n'.join(inputs)
    arguments = [
        '--language', 'english',
        '--ignore_connectivity',
        'existing-mnemonic',
        '--withdrawal_address', withdrawal_address,
        '--folder', my_folder_path,

    ]
    result = runner.invoke(cli, arguments, input=data)

    assert result.exit_code == 0
    assert connectivity_called is False

    clean_key_folder(my_folder_path)


def test_should_not_check_connectivity_with_non_interactive(monkeypatch) -> None:
    connectivity_called = False

    def _mock_socket_getaddrinfo(url, port):
        nonlocal connectivity_called
        connectivity_called = True
        raise OSError()

    monkeypatch.setattr(socket, 'getaddrinfo', _mock_socket_getaddrinfo)

    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_key_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)
    runner = CliRunner()
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'existing-mnemonic',
        '--num_validators', '1',
        '--mnemonic', 'aban aban aban aban aban aban aban aban aban aban aban abou',
        '--validator_start_index', '0',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments)

    assert result.exit_code == 0
    assert connectivity_called is False

    clean_key_folder(my_folder_path)


class _RecordingStderr:
    '''
    A stderr stand-in that records what is written to it and can raise a second
    KeyboardInterrupt from isatty(), simulating a Ctrl+C that lands while click
    is reporting the abort for the first one.

    click's echo() calls should_strip_ansi() -> isatty() before writing, and
    click._compat.isatty() only catches Exception, so a KeyboardInterrupt raised
    there escapes Command.main() entirely. That is where the traceback in
    https://github.com/pallets/click/issues/3802 ended.

    Counting only starts once arm() is called, so `interrupt_at` is relative to
    the abort sequence rather than to any earlier stderr output from the CLI.
    '''

    def __init__(self, interrupt_at: int | None = None):
        self.text = ''
        self.interrupt_at = interrupt_at
        self.isatty_calls = 0
        self.armed = False

    def arm(self) -> None:
        self.armed = True

    def isatty(self) -> bool:
        if self.armed:
            self.isatty_calls += 1
            if self.isatty_calls == self.interrupt_at:
                raise KeyboardInterrupt()
        return False

    def write(self, value: str) -> int:
        self.text += value
        return len(value)

    def flush(self) -> None:
        pass


@pytest.mark.parametrize('interrupt_at', [None, 1])
def test_run_handles_keyboard_interrupt_at_prompt(monkeypatch, interrupt_at) -> None:
    '''
    Ctrl+C at the mnemonic language prompt must exit 1, even if a second
    interrupt arrives while click writes "Aborted!". The message is best effort
    once that happens, but the exit code is not.

    This drives the real `cli` through `run()`: the interrupt is injected where a
    real one lands (click's input function), not by replacing `cli` itself, so
    click's own Abort handling is what is under test.
    '''
    stderr = _RecordingStderr(interrupt_at=interrupt_at)

    def _interrupt_prompt(text: str) -> str:
        stderr.arm()
        raise KeyboardInterrupt()

    monkeypatch.setattr('click.termui.visible_prompt_func', _interrupt_prompt)
    monkeypatch.setattr(sys, 'stderr', stderr)
    monkeypatch.setattr(sys, 'argv', [
        'deposit', '--language', 'english', '--ignore_connectivity', 'generate-mnemonic',
    ])

    try:
        run()
    except SystemExit as e:
        exit_code = e.code
    except KeyboardInterrupt:
        pytest.fail('KeyboardInterrupt escaped click Command.main(); see pallets/click#3802')
    else:
        pytest.fail('run() returned without exiting')

    assert exit_code == 1
    if interrupt_at is None:
        assert 'Aborted!' in stderr.text


def test_should_not_check_connectivity_with_both_non_interactive_or_ignore_connectivity(monkeypatch) -> None:
    connectivity_called = False

    def _mock_socket_getaddrinfo(url, port):
        nonlocal connectivity_called
        connectivity_called = True
        raise OSError()

    monkeypatch.setattr(socket, 'getaddrinfo', _mock_socket_getaddrinfo)

    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    clean_key_folder(my_folder_path)
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)
    runner = CliRunner()
    arguments = [
        '--language', 'english',
        '--non_interactive',
        '--ignore_connectivity',
        'existing-mnemonic',
        '--num_validators', '1',
        '--mnemonic', 'aban aban aban aban aban aban aban aban aban aban aban abou',
        '--mnemonic_password', 'TREZOR',
        '--validator_start_index', '0',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--folder', my_folder_path,
    ]
    result = runner.invoke(cli, arguments)

    assert result.exit_code == 0
    assert connectivity_called is False

    clean_key_folder(my_folder_path)
