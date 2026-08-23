import os
import subprocess  # noqa: S404
import pytest


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
