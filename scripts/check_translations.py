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
    if not isinstance(node, ast.List | ast.Tuple):
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


def relative_translation_path(root: Path, source_file: Path, file_path: ast.AST | None) -> Path:
    value = literal_string(file_path)
    if value is None:
        return source_file.relative_to(root).with_suffix(".json")
    path = Path(value)
    relative = path.relative_to(root) if path.is_absolute() else path
    if relative.parts and relative.parts[0] == "ethstaker_deposit":
        relative = Path(*relative.parts[1:])
    return relative.with_suffix(".json")


def deferred_helpers(root: Path) -> dict[str, tuple[list[str], list[str], dict[str, str | None], list[str]]]:
    helpers: dict[str, tuple[list[str], list[str], dict[str, str | None], list[str]]] = {}
    for source_file in sorted(root.rglob("*.py")):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            parameters = {argument.arg for argument in function.args.args}
            arguments = [argument.arg for argument in function.args.args]
            defaults = (
                dict(zip(arguments[-len(function.args.defaults):], function.args.defaults))
                if function.args.defaults else {}
            )
            file_path_parameters: list[str] = []
            func_parameters: dict[str, str | None] = {}
            prefixes: list[str] = []
            for node in ast.walk(function):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "load_text":
                    continue
                keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
                file_path = keywords.get("file_path")
                if isinstance(file_path, ast.Name) and file_path.id in parameters:
                    file_path_parameters.append(file_path.id)
                func = keywords.get("func")
                if isinstance(func, ast.Name) and func.id in parameters:
                    func_parameters[func.id] = literal_string(defaults.get(func.id))
                if node.args and isinstance(node.args[0], ast.List) and node.args[0].elts:
                    prefix = literal_string(node.args[0].elts[0])
                    if prefix is not None:
                        prefixes.append(prefix)
            if file_path_parameters and func_parameters and prefixes:
                helpers[function.name] = (arguments, file_path_parameters, func_parameters, prefixes)
    return helpers


def deferred_wrappers(
    root: Path,
    helpers: dict[str, tuple[list[str], list[str], dict[str, str | None], list[str]]],
) -> dict[str, tuple[list[str], str]]:
    wrappers: dict[str, tuple[list[str], str]] = {}
    for source_file in sorted(root.rglob("*.py")):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            arguments = [argument.arg for argument in function.args.args]
            for node in ast.walk(function):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                    continue
                if node.func.id not in helpers:
                    continue
                forwarded = [value.id for value in node.args if isinstance(value, ast.Name)]
                if forwarded:
                    wrappers[function.name] = (arguments, node.func.id)
    return wrappers


def translation_references(root: Path) -> tuple[dict[Path, set[str]], dict[Path, set[str]]]:
    references: dict[Path, set[str]] = {}
    dynamic_prefixes: dict[Path, set[str]] = {}
    deferred = deferred_helpers(root)
    wrappers = deferred_wrappers(root, deferred)
    for source_file in sorted(root.rglob("*.py")):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        assigned = assigned_literals(tree)
        assigned_strings_map = assigned_strings(tree)
        function_names = {
            node: node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "load_text":
                continue
            if is_intl_fallback(source_file, node):
                continue
            if any(
                parent.name in deferred and parent.lineno <= node.lineno <= getattr(parent, "end_lineno", parent.lineno)
                for parent in function_names
            ):
                continue
            params = literal_params(node.args[0] if node.args else None)
            if params is None and node.args and isinstance(node.args[0], ast.Name):
                params = assigned.get(node.args[0].id)
            keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
            func = literal_string(keywords.get("func"))
            if func is None and isinstance(keywords.get("func"), ast.Name):
                func = assigned_strings_map.get(keywords["func"].id)
            if params is None or ("func" in keywords and func is None):
                dynamic_func = literal_string(keywords.get("func")) or source_file.stem
                if dynamic_func == source_file.stem:
                    for parent, name in function_names.items():
                        if parent.lineno <= node.lineno <= (getattr(parent, "end_lineno", parent.lineno)):
                            dynamic_func = name
                            break
                relative = relative_translation_path(root, source_file, keywords.get("file_path"))
                dynamic_path = ""
                if node.args and isinstance(node.args[0], ast.List):
                    literal_prefix = literal_string(node.args[0].elts[0]) if node.args[0].elts else None
                    if literal_prefix is not None:
                        dynamic_path = literal_prefix + "."
                dynamic_prefixes.setdefault(relative, set()).add(f"{dynamic_func}.{dynamic_path}")
                continue
            if func is None:
                func = source_file.stem
                for parent, name in function_names.items():
                    if parent.lineno <= node.lineno <= (getattr(parent, "end_lineno", parent.lineno)):
                        func = name
                        break
            relative = relative_translation_path(root, source_file, keywords.get("file_path"))
            references.setdefault(relative, set()).add(".".join([func, *params]))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            deferred_call = deferred.get(node.func.id)
            wrapper = wrappers.get(node.func.id)
            if deferred_call is None and wrapper is not None:
                arguments, helper = wrapper
                deferred_call = deferred[helper]
                node_arguments = dict(zip(arguments, node.args))
                node_arguments.update({keyword.arg: keyword.value for keyword in node.keywords if keyword.arg})
                node = ast.Call(
                    func=node.func,
                    args=[node_arguments.get(name, ast.Constant(value=None)) for name in arguments],
                    keywords=[],
                )
            if deferred_call is None:
                continue
            arguments, _file_path_parameters, func_parameters, prefixes = deferred_call
            values = dict(zip(arguments, node.args))
            values.update({keyword.arg: keyword.value for keyword in node.keywords if keyword.arg})
            file_path = values.get("file_path")
            if not (isinstance(file_path, ast.Name) and file_path.id == "__file__"):
                continue
            dynamic_func = ""
            for parameter, default in func_parameters.items():
                value = values.get(parameter)
                resolved = literal_string(value)
                if resolved is None and isinstance(value, ast.Name):
                    resolved = assigned_strings_map.get(value.id)
                dynamic_func = resolved or default or ""
                if dynamic_func:
                    break
            if not dynamic_func:
                continue
            relative = source_file.relative_to(root).with_suffix(".json")
            for prefix in prefixes:
                dynamic_prefixes.setdefault(relative, set()).add(f"{dynamic_func}.{prefix}.")
    return references, dynamic_prefixes


def main() -> int:
    errors: list[str] = []
    fallback_count = 0
    references, dynamic_prefixes = translation_references(ROOT.parent)
    english_files = sorted((ROOT / "en").rglob("*.json"))
    languages = sorted(p.name for p in ROOT.iterdir() if p.is_dir() and p.name != "en" and p.name != "__pycache__")
    for english_file in english_files:
        source = leaves(json.loads(english_file.read_text(encoding="utf-8")))
        relative = english_file.relative_to(ROOT / "en")
        referenced = references.get(relative, set())
        for key in sorted(set(source) - referenced):
            if any(key.startswith(prefix) for prefix in dynamic_prefixes.get(relative, set())):
                continue
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
        return 1
    print(
        f"Checked {len(languages)} locales against {len(english_files)} English files; "
        f"{fallback_count} English fallbacks remain."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
