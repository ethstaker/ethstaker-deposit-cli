import subprocess  # noqa: S404
import os
import sys
import shutil
import click


def clear_terminal() -> None:
    # Do not clear if running unit tests as stdout can be used to determine state
    if "PYTEST_CURRENT_TEST" in os.environ:
        return

    # We bundle libtinfo via pyinstaller, which messes with the system tput.
    # Remove LD_LIBRARY_PATH just for subprocess.run()
    if sys.platform == 'linux':
        clean_env = os.environ.copy()
        clean_env.pop('LD_LIBRARY_PATH', None)
    elif sys.platform == 'darwin':
        clean_env = os.environ.copy()

    for count in range(2):
        # Call everything twice to complete the clear on iTerm2 and for good measure
        if sys.platform == 'win32':
            # Special-case for asyncio pytest on Windows
            if os.getenv("IS_ASYNC_TEST") == "1":
                click.clear()
            elif shutil.which('clear'):
                subprocess.run(['clear'])  # noqa: S607
            else:
                # cls is a Windows shell builtin and cannot run without a shell.
                subprocess.run('cls', shell=True)  # noqa: S602, S607
        elif sys.platform == 'linux' or sys.platform == 'darwin':
            if shutil.which('clear'):
                subprocess.run(['clear'], env=clean_env)  # noqa: S607
            else:
                click.clear()
            if shutil.which('tput'):
                subprocess.run(['tput', 'reset'], env=clean_env)  # noqa: S607
            if shutil.which('reset'):
                subprocess.run(['reset'], env=clean_env)  # noqa: S607
        else:
            click.clear()
