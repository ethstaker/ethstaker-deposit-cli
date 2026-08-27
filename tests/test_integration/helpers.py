import os
import subprocess  # noqa: S404

from tests.test_integration.interactive import InteractiveProcess


def get_run_script_cmd() -> str:
    return 'bash deposit.sh' if os.name == 'nt' else './deposit.sh'


def build_shell_command(*args: str) -> str:
    '''
    Join CLI arguments into a single shell command string.

    The first argument is the executable invocation (for example
    `bash deposit.sh`) and is used verbatim. Remaining arguments containing
    whitespace are wrapped in double quotes so that values like mnemonics
    survive both cmd.exe (Windows CI) and bash unquoting.
    '''
    if not args:
        return ''
    command, *rest = args
    return ' '.join([command] + [f'"{arg}"' if ' ' in arg else arg for arg in rest])


async def run_deposit_cli(*args: str) -> list[str]:
    '''
    Run the CLI through deposit.sh as a subprocess and assert a zero exit code.

    Returns the transcript of the subprocess output.
    '''
    cmd = build_shell_command(get_run_script_cmd(), *args)
    async with InteractiveProcess(cmd) as process:
        await process.wait()
    return process.transcript


def run_deposit_cli_capture(*args: str) -> subprocess.CompletedProcess:
    '''
    Run the CLI through deposit.sh as a subprocess and return the completed
    process with stdout/stderr captured separately, without asserting the exit
    code. Used by failure-mode tests.
    '''
    cmd = build_shell_command(get_run_script_cmd(), *args)
    return subprocess.run(cmd, shell=True, capture_output=True)  # noqa: S602
