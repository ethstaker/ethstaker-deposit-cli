import json
from pathlib import Path

from scripts.check_translations import ROOT, leaves, translation_references


def test_leaves_flattens_nested_values() -> None:
    assert leaves({'root': {'child': 'value'}}) == {'root.child': 'value'}


def test_translation_references_resolves_literal_calls(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    package.mkdir()
    source = package / 'feature.py'
    source.write_text(
        'from ethstaker_deposit.utils.intl import load_text\n'
        'def render():\n'
        "    return load_text(['message', 'prompt'])\n",
        encoding='utf-8',
    )

    references, warnings = translation_references(package)

    assert references == {Path('feature.json'): {'render.message.prompt'}}
    assert warnings == []


def test_translation_references_resolves_explicit_file_and_function(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    package.mkdir()
    source = package / 'feature.py'
    source.write_text(
        'from ethstaker_deposit.utils.intl import load_text\n'
        "load_text(['message'], file_path='ethstaker_deposit/shared.json', func='shared')\n",
        encoding='utf-8',
    )

    references, warnings = translation_references(package)

    assert references == {Path('shared.json'): {'shared.message'}}
    assert warnings == []


def test_translation_references_warns_for_dynamic_calls(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    package.mkdir()
    source = package / 'feature.py'
    source_text = (
        'from ethstaker_deposit.utils.intl import load_text\n'
        'params = get_params()\n'
        'load_text(params)\n'
    )
    source.write_text(source_text, encoding='utf-8')

    references, warnings = translation_references(package)

    assert references == {}
    load_text_line = source_text.splitlines().index('load_text(params)') + 1
    assert warnings == [f'ethstaker_deposit/feature.py:{load_text_line}: dynamic load_text reference']


def test_translation_references_ignores_intl_fallback(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    intl = package / 'utils'
    intl.mkdir(parents=True)
    source = intl / 'intl.py'
    source.write_text(
        'def load_text(params, file_path, func, lang):\n'
        '    return load_text(params, file_path, func, "en")\n',
        encoding='utf-8',
    )

    references, warnings = translation_references(package)

    assert references == {}
    assert warnings == []


def test_repository_has_no_orphaned_english_keys() -> None:
    references, warnings = translation_references(ROOT.parent)
    assert warnings == []
    for english_file in (ROOT / 'en').rglob('*.json'):
        relative = english_file.relative_to(ROOT / 'en')
        assert set(leaves(json.loads(english_file.read_text(encoding='utf-8')))) <= references.get(relative, set())
