import os
import subprocess  # noqa: S404
import pytest

from tests.shared_helpers import clean_folder


@pytest.fixture(scope='session')
def deposit_cli_installed() -> None:
    '''
    Install the CLI dependencies once per test session, instead of every
    subprocess-based test running `deposit.sh install` itself.
    '''
    run_script_cmd = 'bash deposit.sh' if os.name == 'nt' else './deposit.sh'
    result = subprocess.run(  # noqa: S602
        run_script_cmd + ' install',
        shell=True,
        capture_output=True,
    )
    assert result.returncode == 0, (
        f'{run_script_cmd} install failed with code {result.returncode}\n'
        f'--- stdout ---\n{result.stdout.decode(errors="replace")[-4000:]}\n'
        f'--- stderr ---\n{result.stderr.decode(errors="replace")[-2000:]}'
    )


@pytest.fixture
def cli_output_folder(tmp_path) -> str:
    '''
    A fresh, existing output folder for CLI integration tests.

    Cleaned up with the project's Windows-safe rmtree so read-only keystore
    files are removed on every platform.
    '''
    folder = tmp_path / 'output'
    folder.mkdir()
    yield str(folder)
    clean_folder(str(tmp_path), str(folder), ignore_primary=True)
