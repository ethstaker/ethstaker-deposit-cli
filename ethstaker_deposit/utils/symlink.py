import os

import click

from ethstaker_deposit.utils import config
from ethstaker_deposit.utils.intl import load_text


TEXT_FILE_PATH = __file__.replace('.py', '.json')


def warn_if_output_directory_symlink(output_directory: str) -> None:
    """Warn before writing through a symlink in the output path."""
    if config.non_interactive:
        return

    absolute_path = os.path.abspath(output_directory)
    drive, path = os.path.splitdrive(absolute_path)
    current_path = drive + os.sep if drive else os.sep

    for component in path.strip(os.sep).split(os.sep):
        current_path = os.path.join(current_path, component)
        if os.path.islink(current_path):
            click.echo(load_text(
                ['warning'],
                file_path=TEXT_FILE_PATH,
                func='warn_if_output_directory_symlink',
            ).format(path=current_path, target=os.path.realpath(current_path)))
            if not click.confirm(load_text(
                    ['prompt'],
                    file_path=TEXT_FILE_PATH,
                    func='warn_if_output_directory_symlink',
            ), default=False):
                raise click.Abort()
            return
