import pytest

from scripts.check_python_version import check_python_version, is_supported, read_requires_python


def test_reads_project_python_requirement() -> None:
    assert read_requires_python('pyproject.toml') == '>=3.11,<4'


@pytest.mark.parametrize(
    ('version', 'expected'),
    [
        ((3, 10), False),
        ((3, 11), True),
        ((3, 14), True),
        ((4, 0), False),
    ],
)
def test_is_supported(version: tuple[int, int], expected: bool) -> None:
    assert is_supported(version, '>=3.11,<4') is expected


def test_check_python_version_reports_requirement(tmp_path, capsys) -> None:
    pyproject = tmp_path / 'pyproject.toml'
    pyproject.write_text('requires-python = ">=3.12,<4"\n', encoding='utf-8')

    assert not check_python_version(pyproject, (3, 11))
    assert 'Required Python versions: >=3.12,<4' in capsys.readouterr().err
