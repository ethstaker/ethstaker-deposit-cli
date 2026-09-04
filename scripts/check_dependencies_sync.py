#!/usr/bin/env python3
"""Verify that pyproject.toml dependency constraints are satisfied by the pip lockfiles.

The runtime/executable path installs from the pinned, hashed lockfiles
(requirements.txt, requirements_test.txt), while the library metadata lives in
pyproject.toml and uses >= floor ranges. This check ensures the two never
silently diverge:

  1. Every dependency declared in pyproject.toml must appear in the
     corresponding lockfile.
  2. Every pin in those lockfiles must satisfy the range declared in
     pyproject.toml (so the locked set is always installable given the
     declared ranges).

Build-only requirements under build_configs/* are intentionally not checked,
as they are independent of pyproject.toml.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MARKER_RE = re.compile(r"\s*;\s*.*$")
CONSTRAINT_RE = re.compile(r"^([^<>=!~;]+)\s*(.*)$")
VERSION_OP_RE = re.compile(r"^(==|!=|<=|>=|<|>|~=|===)?\s*([0-9][A-Za-z0-9._*+-]*)$")


def normalize(name: str) -> str:
    """PEP 503 normalisation: lowercase and replace runs of -/_. with -."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_deps(entries: list[str]) -> dict[str, list[tuple[str, str]]]:
    """Return {dep_name: [(op, version), ...]} for a list of dep specifiers."""
    declared: dict[str, list[tuple[str, str]]] = {}
    for entry in entries:
        entry = MARKER_RE.sub("", entry).strip()
        match = CONSTRAINT_RE.match(entry)
        if not match:
            continue
        name = normalize(match.group(1).strip())
        spec = match.group(2).strip()
        constraints = declared.setdefault(name, [])
        if not spec:
            continue
        vm = VERSION_OP_RE.match(spec)
        if vm:
            constraints.append((vm.group(1) or "==", vm.group(2)))
    return declared


def parse_pyproject_deps() -> tuple[dict[str, list[tuple[str, str]]], dict[str, list[tuple[str, str]]]]:
    """Return (runtime_deps, test_deps) as {name: [(op, version), ...]}."""
    with (ROOT / "pyproject.toml").open("rb") as f:
        data = tomllib.load(f)
    project = data["project"]
    runtime = parse_deps(list(project.get("dependencies", [])))
    test = parse_deps(list(project.get("optional-dependencies", {}).get("test", [])))
    return runtime, test


def parse_lockfile(path: Path) -> dict[str, str]:
    """Return {dep_name: pinned_version} from a pip lockfile."""
    pins: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-r", "--")):
            continue
        if line.startswith("-"):
            continue
        if "==" not in line:
            continue
        name, _, version = line.partition("==")
        name = normalize(name.strip())
        version = version.split("\\")[0].strip().split(";")[0].strip()
        pins[name] = version
    return pins


def version_tuple(v: str) -> tuple:
    nums = re.split(r"[^0-9]+", v)
    parts = []
    for n in nums:
        try:
            parts.append(int(n))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def satisfied(op: str | None, wanted: str, pinned: str) -> bool:
    """Check whether `pinned` satisfies `op wanted`."""
    if op is None or op == "==":
        return pinned == wanted
    if op == ">=":
        return version_tuple(pinned) >= version_tuple(wanted)
    if op == ">":
        return version_tuple(pinned) > version_tuple(wanted)
    if op == "<=":
        return version_tuple(pinned) <= version_tuple(wanted)
    if op == "<":
        return version_tuple(pinned) < version_tuple(wanted)
    if op == "!=":
        return pinned != wanted
    if op == "~=":
        return version_tuple(pinned)[:2] == version_tuple(wanted)[:2] and version_tuple(
            pinned
        ) >= version_tuple(wanted)
    if op == "===":
        return pinned == wanted
    return False


def check(declared: dict[str, list[tuple[str, str]]], pins: dict[str, str], label: str) -> list[str]:
    errors: list[str] = []
    for name, constraints in sorted(declared.items()):
        if name not in pins:
            errors.append(f"{label}: dependency '{name}' declared in pyproject.toml is missing from the lockfile")
            continue
        pinned = pins[name]
        for op, wanted in constraints:
            if not satisfied(op, wanted, pinned):
                errors.append(
                    f"{label}: pinned {name}=={pinned} does not satisfy '{name} {op} {wanted}' from pyproject.toml"
                )
    return errors


def main() -> int:
    runtime, test = parse_pyproject_deps()
    errors: list[str] = []
    errors.extend(check(runtime, parse_lockfile(ROOT / "requirements.txt"), "requirements.txt"))
    errors.extend(check(test, parse_lockfile(ROOT / "requirements_test.txt"), "requirements_test.txt"))
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        print("\nRegenerate the lockfile and update pyproject.toml in sync.", file=sys.stderr)
        return 1
    print("OK: pyproject.toml constraints are satisfied by the lockfiles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
