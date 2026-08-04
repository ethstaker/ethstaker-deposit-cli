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

    references, dynamic_prefixes = translation_references(package)

    assert references == {Path('feature.json'): {'render.message.prompt'}}
    assert dynamic_prefixes == {}


def test_translation_references_resolves_explicit_file_and_function(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    package.mkdir()
    source = package / 'feature.py'
    source.write_text(
        'from ethstaker_deposit.utils.intl import load_text\n'
        "load_text(['message'], file_path='ethstaker_deposit/shared.json', func='shared')\n",
        encoding='utf-8',
    )

    references, dynamic_prefixes = translation_references(package)

    assert references == {Path('shared.json'): {'shared.message'}}
    assert dynamic_prefixes == {}


def test_translation_references_ignores_dynamic_calls(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    package.mkdir()
    source = package / 'feature.py'
    source_text = (
        'from ethstaker_deposit.utils.intl import load_text\n'
        'params = get_params()\n'
        'load_text(params)\n'
    )
    source.write_text(source_text, encoding='utf-8')

    references, dynamic_prefixes = translation_references(package)

    assert references == {}
    assert dynamic_prefixes == {Path('feature.json'): {'feature.'}}


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

    references, dynamic_prefixes = translation_references(package)

    assert references == {}
    assert dynamic_prefixes == {}


def test_translation_references_marks_dynamic_validation_file(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    utils = package / 'utils'
    utils.mkdir(parents=True)
    source = utils / 'validation.py'
    source.write_text(
        'from ethstaker_deposit.utils.intl import load_text\n'
        'def _decode_fixed_hex(message_key):\n'
        "    return load_text(['dynamic', message_key], func='validate_devnet_chain_setting_json')\n",
        encoding='utf-8',
    )

    references, dynamic_prefixes = translation_references(package)

    assert references == {}
    assert dynamic_prefixes == {Path('utils/validation.json'): {'validate_devnet_chain_setting_json.dynamic.'}}


def test_translation_references_resolves_dunder_file_for_dynamic_call(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    cli = package / 'cli'
    cli.mkdir(parents=True)
    source = cli / 'generate_keys.py'
    source.write_text(
        'from ethstaker_deposit.utils.intl import load_text\n'
        "chain_text_key = 'chain'\n"
        "load_text(['dynamic', chain_text_key, 'help'], file_path=__file__, "
        "func='generate_keys_arguments_decorator')\n",
        encoding='utf-8',
    )

    references, dynamic_prefixes = translation_references(package)

    assert references == {}
    assert dynamic_prefixes == {Path('cli/generate_keys.json'):
                                {'generate_keys_arguments_decorator.dynamic.'}}


def test_translation_references_defers_dynamic_call_to_dunder_file_caller(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    utils = package / 'utils'
    cli = package / 'cli'
    utils.mkdir(parents=True)
    cli.mkdir()
    (utils / 'helpers.py').write_text(
        'from ethstaker_deposit.utils.intl import load_text\n'
        "def argument_decorator(file_path, func='default_decorator'):\n"
        "    return load_text(['dynamic', get_key(), 'help'], file_path=file_path, func=func)\n",
        encoding='utf-8',
    )
    (cli / 'feature.py').write_text(
        'from ethstaker_deposit.utils.helpers import argument_decorator\n'
        "*argument_decorator(file_path=__file__)\n",
        encoding='utf-8',
    )

    references, dynamic_prefixes = translation_references(package)

    assert references == {}
    assert dynamic_prefixes == {Path('cli/feature.json'): {'default_decorator.dynamic.'}}


def test_translation_references_deferred_literal_func_overrides_default(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    utils = package / 'utils'
    cli = package / 'cli'
    utils.mkdir(parents=True)
    cli.mkdir()
    (utils / 'helpers.py').write_text(
        'from ethstaker_deposit.utils.intl import load_text\n'
        "def argument_decorator(file_path, func='default_decorator'):\n"
        "    return load_text(['dynamic', get_key()], file_path=file_path, func=func)\n",
        encoding='utf-8',
    )
    (cli / 'feature.py').write_text(
        'from ethstaker_deposit.utils.helpers import argument_decorator\n'
        "argument_decorator(file_path=__file__, func='feature_decorator')\n",
        encoding='utf-8',
    )

    _, dynamic_prefixes = translation_references(package)

    assert dynamic_prefixes == {Path('cli/feature.json'): {'feature_decorator.dynamic.'}}


def test_translation_references_resolves_positional_named_func(tmp_path: Path) -> None:
    package = tmp_path / 'ethstaker_deposit'
    utils = package / 'utils'
    cli = package / 'cli'
    utils.mkdir(parents=True)
    cli.mkdir()
    (utils / 'helpers.py').write_text(
        'from ethstaker_deposit.utils.intl import load_text\n'
        "def argument_decorator(func='default_decorator', file_path='', chain_text_key='chain'):\n"
        "    return load_text(['dynamic', chain_text_key], file_path=file_path, func=func)\n",
        encoding='utf-8',
    )
    (cli / 'feature.py').write_text(
        'from ethstaker_deposit.utils.helpers import argument_decorator\n'
        "FUNC_NAME = 'feature_decorator'\n"
        "@argument_decorator(FUNC_NAME, __file__, 'arg_chain')\n"
        'def command():\n'
        '    pass\n',
        encoding='utf-8',
    )

    _, dynamic_prefixes = translation_references(package)

    assert dynamic_prefixes == {Path('cli/feature.json'): {'feature_decorator.dynamic.'}}


def test_repository_has_no_orphaned_english_keys() -> None:
    references, dynamic_prefixes = translation_references(ROOT.parent)
    for english_file in (ROOT / 'en').rglob('*.json'):
        relative = english_file.relative_to(ROOT / 'en')
        missing = set(leaves(json.loads(english_file.read_text(encoding='utf-8')))) - references.get(relative, set())
        assert not {
            key for key in missing
            if not any(key.startswith(prefix) for prefix in dynamic_prefixes.get(relative, set()))
        }
