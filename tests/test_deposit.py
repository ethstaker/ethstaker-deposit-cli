import os
import socket

import click
import pytest
from click.testing import CliRunner

from ethstaker_deposit import deposit
from ethstaker_deposit.deposit import check_connectivity, cli, run
from ethstaker_deposit.utils import config
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


def test_connectivity_warning_uses_selected_language(monkeypatch) -> None:
    # The warning is emitted from the group callback, which must record the chosen
    # language before running the connectivity check, or load_text falls back to English.
    paused_text = None

    def _mock_click_pause(text):
        nonlocal paused_text
        paused_text = text

    def _mock_socket_getaddrinfo(url, port):
        return True

    monkeypatch.setattr(click, 'pause', _mock_click_pause)
    monkeypatch.setattr(socket, 'getaddrinfo', _mock_socket_getaddrinfo)
    # config.language is a module global that nothing else in the suite resets.
    monkeypatch.setattr(config, 'language', 'en')

    runner = CliRunner()
    arguments = [
        '--language', 'german',
        'generate-mnemonic',
    ]
    result = runner.invoke(cli, arguments, input='english\n')

    assert result.exit_code == 0
    assert paused_text is not None
    assert 'Internetverbindung erkannt' in paused_text


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


def test_run_handles_keyboard_interrupt_from_cli(monkeypatch, capsys) -> None:
    # Simulates a KeyboardInterrupt escaping click's own Abort handling
    # (see click's `except Abort:` block in `BaseCommand.main`), which can
    # happen if a second interrupt fires while click is echoing "Aborted!".
    def _mock_cli():
        raise KeyboardInterrupt()

    monkeypatch.setattr(deposit, 'cli', _mock_cli)

    with pytest.raises(SystemExit) as exc_info:
        run()

    assert exc_info.value.code == 1
    assert 'Aborted!' in capsys.readouterr().err


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
