#!/usr/bin/env python3
"""Check locale completeness and placeholder preservation against English."""

from __future__ import annotations

import json
import ast
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1] / "ethstaker_deposit" / "intl"
PLACEHOLDER = re.compile(r"\{[^{}]+\}")


def leaves(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            result.update(leaves(child, f"{prefix}.{key}" if prefix else key))
        return result
    return {prefix: value}


def literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def literal_params(node: ast.AST | None) -> list[str] | None:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    values = [literal_string(element) for element in node.elts]
    return values if all(value is not None for value in values) else None


def assigned_literals(tree: ast.AST) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        params = literal_params(node.value)
        if params is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    values[target.id] = params
    return values


def assigned_strings(tree: ast.AST) -> dict[str, str]:
    values: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value = literal_string(node.value)
        if value is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    values[target.id] = value
    return values


def is_intl_fallback(source_file: Path, node: ast.Call) -> bool:
    return (
        source_file.parts[-3:] == ("ethstaker_deposit", "utils", "intl.py")
        and len(node.args) == 4
        and all(isinstance(argument, ast.Name) for argument in node.args[:3])
        and literal_string(node.args[3]) == "en"
    )


def translation_references(root: Path) -> tuple[dict[Path, set[str]], list[str]]:
    references: dict[Path, set[str]] = {}
    warnings: list[str] = []
    for source_file in sorted(root.rglob("*.py")):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        assigned = assigned_literals(tree)
        assigned_strings_map = assigned_strings(tree)
        function_names = {
            node: node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "load_text":
                continue
            if is_intl_fallback(source_file, node):
                continue
            params = literal_params(node.args[0] if node.args else None)
            if params is None and node.args and isinstance(node.args[0], ast.Name):
                params = assigned.get(node.args[0].id)
            keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
            func = literal_string(keywords.get("func"))
            if func is None and isinstance(keywords.get("func"), ast.Name):
                func = assigned_strings_map.get(keywords["func"].id)
            if params is None or ("func" in keywords and func is None):
                source_name = source_file.relative_to(root.parent).as_posix()
                warnings.append(f"{source_name}:{node.lineno}: dynamic load_text reference")
                continue
            if func is None:
                func = source_file.stem
                for parent, name in function_names.items():
                    if parent.lineno <= node.lineno <= (getattr(parent, "end_lineno", parent.lineno)):
                        func = name
                        break
            file_path = literal_string(keywords.get("file_path"))
            if file_path is None:
                relative = source_file.relative_to(root).with_suffix(".json")
            else:
                file_path_path = Path(file_path)
                relative = file_path_path.relative_to(root) if file_path_path.is_absolute() else file_path_path
                if relative.parts and relative.parts[0] == "ethstaker_deposit":
                    relative = Path(*relative.parts[1:])
                if relative.suffix != ".json":
                    relative = relative.with_suffix(".json")
            references.setdefault(relative, set()).add(".".join([func, *params]))
    return references, warnings


def main() -> int:
    errors: list[str] = []
    fallback_count = 0
    references, warnings = translation_references(ROOT.parent)
    english_files = sorted((ROOT / "en").rglob("*.json"))
    languages = sorted(p.name for p in ROOT.iterdir() if p.is_dir() and p.name != "en" and p.name != "__pycache__")
    for english_file in english_files:
        source = leaves(json.loads(english_file.read_text(encoding="utf-8")))
        relative = english_file.relative_to(ROOT / "en")
        referenced = references.get(relative, set())
        for key in sorted(set(source) - referenced):
            errors.append(f"orphaned key {relative}:{key}")
    for language in languages:
        for english_file in english_files:
            relative = english_file.relative_to(ROOT / "en")
            target = ROOT / language / relative
            if not target.exists():
                errors.append(f"{language}: missing file {relative}")
                continue
            source = leaves(json.loads(english_file.read_text(encoding="utf-8")))
            translated = leaves(json.loads(target.read_text(encoding="utf-8")))
            for key, text in source.items():
                if key not in translated:
                    errors.append(f"{language}: missing key {relative}:{key}")
                    continue
                if PLACEHOLDER.findall(str(text)) != PLACEHOLDER.findall(str(translated[key])):
                    errors.append(f"{language}: placeholder mismatch {relative}:{key}")
                if translated[key] == text:
                    fallback_count += 1
    if errors:
        print("\n".join(errors))
        if warnings:
            print("\n".join(f"warning: {warning}" for warning in warnings))
        return 1
    if warnings:
        print("\n".join(f"warning: {warning}" for warning in warnings))
    print(
        f"Checked {len(languages)} locales against {len(english_files)} English files; "
        f"{fallback_count} English fallbacks remain."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
