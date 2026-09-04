#!/usr/bin/env python3
"""Fill missing locale keys with English fallbacks while preserving translations.

The runtime already falls back to ``intl/en`` for absent keys. This script makes
that fallback explicit for translators and keeps locale JSON files structurally
complete without pretending that English fallback text is translated.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1] / "ethstaker_deposit" / "intl"
LANGUAGES = ("ar", "de", "el", "fr", "id", "it", "ja", "ko", "pt-BR", "ro", "tr", "zh-CN")


def leaves(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            result.update(leaves(child, f"{prefix}.{key}" if prefix else key))
        return result
    return {prefix: value}


def set_leaf(value: dict[str, Any], path: str, replacement: str) -> None:
    parts = path.split(".")
    current: dict[str, Any] = value
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = replacement


def main() -> None:
    english_files = sorted((ROOT / "en").rglob("*.json"))
    for language in LANGUAGES:
        for english_file in english_files:
            relative = english_file.relative_to(ROOT / "en")
            target = ROOT / language / relative
            english = json.loads(english_file.read_text(encoding="utf-8"))
            translated = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
            existing = leaves(translated)
            for path, source in leaves(english).items():
                if path in existing:
                    continue
                set_leaf(translated, path, source)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(translated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
