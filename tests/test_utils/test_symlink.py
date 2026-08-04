import os

import click
import pytest

from ethstaker_deposit.utils import config
from ethstaker_deposit.utils.symlink import warn_if_output_directory_symlink


@pytest.mark.skipif(not hasattr(os, 'symlink'), reason='Symbolic links are not supported')
def test_symlink_warning_allows_intentionally_created_link(tmp_path, monkeypatch, capsys) -> None:
    target = tmp_path / 'target'
    target.mkdir()
    link = tmp_path / 'output'
    link.symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(click, 'confirm', lambda *args, **kwargs: True)
    monkeypatch.setattr(config, 'non_interactive', False)

    warn_if_output_directory_symlink(str(link / 'generated'))

    output = capsys.readouterr().out
    assert 'WARNING: Output directory contains a symbolic link' in output
    assert str(target) in output


@pytest.mark.skipif(not hasattr(os, 'symlink'), reason='Symbolic links are not supported')
def test_symlink_warning_aborts_by_default(tmp_path, monkeypatch) -> None:
    target = tmp_path / 'target'
    target.mkdir()
    link = tmp_path / 'output'
    link.symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(click, 'confirm', lambda *args, **kwargs: False)
    monkeypatch.setattr(config, 'non_interactive', False)

    with pytest.raises(click.Abort):
        warn_if_output_directory_symlink(str(link / 'generated'))


def test_symlink_warning_is_skipped_non_interactive(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, 'non_interactive', True)
    monkeypatch.setattr(os.path, 'islink', lambda path: pytest.fail('islink should not be called'))

    warn_if_output_directory_symlink(str(tmp_path / 'output'))
