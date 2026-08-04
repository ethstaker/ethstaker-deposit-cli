"""Check an interpreter against the project's requires-python metadata."""

from __future__ import annotations
import re
import sys
from pathlib import Path
from typing import Sequence


VERSION_SPECIFIER = re.compile(r'(?P<operator>>=|<)\s*(?P<major>\d+)(?:\.(?P<minor>\d+))?')


def read_requires_python(pyproject_path: str | Path) -> str:
    for line in Path(pyproject_path).read_text(encoding='utf-8').splitlines():
        if line.strip().startswith('requires-python'):
            _, value = line.split('=', 1)
            return value.strip().strip('"')
    raise ValueError(f'No requires-python declaration found in {pyproject_path}')


def parse_bounds(requirement: str) -> tuple[tuple[int, int], tuple[int, int] | None]:
    lower_bound: tuple[int, int] | None = None
    upper_bound: tuple[int, int] | None = None
    for match in VERSION_SPECIFIER.finditer(requirement):
        version = (int(match['major']), int(match['minor'] or 0))
        if match['operator'] == '>=':
            lower_bound = version
        else:
            upper_bound = version

    if lower_bound is None:
        raise ValueError(f'No supported lower Python bound found in {requirement}')
    return lower_bound, upper_bound


def is_supported(version: Sequence[int], requirement: str) -> bool:
    lower_bound, upper_bound = parse_bounds(requirement)
    current = (version[0], version[1])
    return current >= lower_bound and (upper_bound is None or current < upper_bound)


def check_python_version(pyproject_path: str | Path, version: Sequence[int] = sys.version_info) -> bool:
    requirement = read_requires_python(pyproject_path)
    if is_supported(version, requirement):
        return True

    print(
        f'Python {version[0]}.{version[1]} is not supported by this release. '
        f'Required Python versions: {requirement}',
        file=sys.stderr,
    )
    return False


def main() -> int:
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} PYPROJECT_PATH', file=sys.stderr)
        return 2
    try:
        return 0 if check_python_version(sys.argv[1]) else 1
    except (OSError, ValueError) as error:
        print(f'Unable to determine supported Python versions: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
