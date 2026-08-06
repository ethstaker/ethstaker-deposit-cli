from scripts.check_python_version import (
    check_python_version,
    is_supported,
    parse_bounds,
    read_requires_python,
)


def test_reads_project_python_requirement() -> None:
    requirement = read_requires_python('pyproject.toml')
    assert parse_bounds(requirement)[0] is not None


def test_is_supported_at_project_boundaries() -> None:
    requirement = read_requires_python('pyproject.toml')
    lower_bound, upper_bound = parse_bounds(requirement)

    assert is_supported((lower_bound[0], lower_bound[1] - 1), requirement) is False
    assert is_supported(lower_bound, requirement) is True
    assert is_supported((lower_bound[0], lower_bound[1] + 1), requirement) is True

    if upper_bound is not None:
        assert is_supported((upper_bound[0], upper_bound[1] - 1), requirement) is True
        assert is_supported(upper_bound, requirement) is False


def test_check_python_version_reports_requirement(tmp_path, capsys) -> None:
    pyproject = tmp_path / 'pyproject.toml'
    pyproject.write_text('requires-python = ">=3.12,<4"\n', encoding='utf-8')

    assert not check_python_version(pyproject, (3, 11))
    assert 'Required Python versions: >=3.12,<4' in capsys.readouterr().err
