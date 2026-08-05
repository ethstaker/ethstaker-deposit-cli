#!/usr/bin/env python3
"""Check locale completeness and placeholder preservation against English."""

from __future__ import annotations

import json
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


def main() -> int:
    errors: list[str] = []
    fallback_count = 0
    english_files = sorted((ROOT / "en").rglob("*.json"))
    languages = sorted(p.name for p in ROOT.iterdir() if p.is_dir() and p.name != "en" and p.name != "__pycache__")
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
    print(f"Checked {len(languages)} locales against {len(english_files)} English files; {fallback_count} English fallbacks remain.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
