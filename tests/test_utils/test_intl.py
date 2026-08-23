import os
import pytest

from ethstaker_deposit.utils.constants import (
    INTL_LANG_OPTIONS,
    MNEMONIC_LANG_OPTIONS,
)
from ethstaker_deposit.utils.intl import (
    _resolve_rel_path,
    fuzzy_reverse_dict_lookup,
    get_first_options,
    load_text,
)


@pytest.mark.parametrize(
    'params, file_path, func, lang, found_str', [
        (['arg_mnemonic_language', 'prompt'], os.path.join('ethstaker_deposit', 'cli', 'new_mnemonic.json'),
         'new_mnemonic', 'en', 'Please choose the language of the mnemonic word list'),
        (['arg_mnemonic_language', 'prompt'], os.path.join('ethstaker_deposit', 'cli', 'new_mnemonic.json'),
         'new_mnemonic', 'ja', 'ニーモニックの言語を選択してください'),
    ]
)
def test_load_text(params: list[str], file_path: str, func: str, lang: str, found_str: str) -> None:
    assert found_str in load_text(params, file_path, func, lang)


def test_load_text_source_path_matches_json_path() -> None:
    params = ['arg_mnemonic_language', 'prompt']
    func = 'new_mnemonic'
    source_path = os.path.join('ethstaker_deposit', 'cli', 'new_mnemonic.py')
    json_path = os.path.join('ethstaker_deposit', 'cli', 'new_mnemonic.json')

    assert load_text(params, source_path, func, 'en') == load_text(params, json_path, func, 'en')


def test_load_text_frozen_basename_uses_module_translation() -> None:
    assert 'connectivity' in load_text(['connectivity_warning'], 'deposit.py', 'check_connectivity', 'en').lower()


class _FakeFrame:
    f_globals: dict


class _FakeCaller:
    def __init__(self, module_name: str) -> None:
        frame = _FakeFrame()
        frame.f_globals = {'__name__': module_name}
        self.frame = frame


@pytest.mark.parametrize(
    'module_name, expected', [
        ('ethstaker_deposit.cli.new_mnemonic', ['cli', 'new_mnemonic.json']),
        ('ethstaker_deposit.utils.intl', ['utils', 'intl.json']),
        ('ethstaker_deposit.cli.sub.new_mnemonic', ['cli', 'sub', 'new_mnemonic.json']),
    ]
)
def test_resolve_rel_path_auto_detected(module_name: str, expected: list[str]) -> None:
    assert _resolve_rel_path(_FakeCaller(module_name), file_path='', auto_detected=True) == expected


@pytest.mark.parametrize(
    'params, file_path, func, lang, valid', [
        (['arg_mnemonic_language', 'prompt'], os.path.join('ethstaker_deposit', 'cli', 'new_mnemonic.json'),
         'new_mnemonic', 'zz', True),  # invalid language, should revert to english
        (['arg_mnemonic_language'], os.path.join('ethstaker_deposit', 'cli', 'new_mnemonic.json'),
         'new_mnemonic', 'en', False),  # incomplete params
        (['arg_mnemonic_language', 'prompt'], os.path.join('ethstaker_deposit', 'cli', 'invalid.json'),
         'new_mnemonic', 'en', False),  # invalid json path
        (['arg_mnemonic_language', 'prompt'], os.path.join('ethstaker_deposit', 'cli', 'invalid.json'),
         'new_mnemonic', 'zz', False),  # invalid json path in invalid language
    ]
)
def test_load_text_en_fallover(params: list[str], file_path: str, func: str, lang: str, valid: bool) -> None:
    if valid:
        assert load_text(params, file_path, func, lang) == load_text(params, file_path, func, 'en')
    else:
        try:
            load_text(params, file_path, func, lang)
        except KeyError:
            pass
        else:
            assert False


@pytest.mark.parametrize(
    'options, first_options', [
        ({'a': ['a', 1], 'b': range(5), 'c': [chr(i) for i in range(65, 90)]}, ['a', 0, 'A']),
    ]
)
def test_get_first_options(options, first_options):
    assert get_first_options(options) == first_options


@pytest.mark.parametrize(
    'test, match, options', [
        ('English', 'english', MNEMONIC_LANG_OPTIONS),
        ('한국어', 'korean', MNEMONIC_LANG_OPTIONS),
        ('Deutsch', 'de', INTL_LANG_OPTIONS),
        ('Roman', 'ro', INTL_LANG_OPTIONS),
    ]
)
def test_fuzzy_reverse_dict_lookup(test, match, options):
    assert fuzzy_reverse_dict_lookup(test, options) == match
