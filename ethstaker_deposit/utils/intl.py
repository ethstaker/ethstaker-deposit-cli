import inspect
import difflib
import json
from typing import Any
from collections.abc import Iterable, Mapping, Sequence
import os

from ethstaker_deposit.utils import config
from ethstaker_deposit.utils.constants import (
    INTL_CONTENT_PATH,
)
from ethstaker_deposit.utils.file_handling import (
    resource_path,
)
from ethstaker_deposit.exceptions import ValidationError


def _get_from_dict(dataDict: dict[str, Any], mapList: Iterable[str]) -> str:
    '''
    Iterate nested dictionaries
    '''
    try:
        # Unbound dict.get keeps the existing contract: a missing key yields None and a
        # non-dict intermediate raises TypeError, both of which surface below as KeyError.
        ans: Any = dataDict
        for key in mapList:
            ans = dict.get(ans, key)
        if not isinstance(ans, str):
            raise ValidationError('Incomplete')
        return ans
    except TypeError:
        raise KeyError(f'{mapList} not in internationalisation json file.')
    except ValidationError:
        raise KeyError(f'The provided params ({mapList}) were incomplete.')


_ROOT_PACKAGE = os.path.dirname(INTL_CONTENT_PATH)


def _resolve_rel_path(caller: Any, file_path: str, auto_detected: bool) -> list[str]:
    '''
    Resolve the intl JSON path (relative to INTL_CONTENT_PATH/<lang>) for a load_text call.
    '''
    # Auto-detected calls use the caller's module name, which frozen builds preserve even
    # when the reported file name collapses to a bare basename (for example, deposit.py).
    module_name = caller.frame.f_globals.get('__name__', '')
    if auto_detected and module_name.startswith(_ROOT_PACKAGE + '.'):
        rel_path_list = module_name.split('.')[1:]
        rel_path_list[-1] += '.json'
        return rel_path_list

    file_path_list = os.path.normpath(file_path).split(os.path.sep)
    if _ROOT_PACKAGE in file_path_list:
        last_occurrence = len(file_path_list) - file_path_list[::-1].index(_ROOT_PACKAGE)
        return file_path_list[last_occurrence:]
    return [os.path.basename(file_path)]


def load_text(params: list[str], file_path: str = '', func: str = '', lang: str = '') -> str:
    '''
    Determine and return the appropriate internationalisation text for a given set of `params`.
    '''
    caller = inspect.stack()[1]
    auto_detected = file_path == ''

    if auto_detected:
        # Auto-detect file-path based on call stack
        file_path = caller.filename
        if file_path[-4:] == '.pyc':
            file_path = file_path[:-4] + '.json'  # replace .pyc with .json
        elif file_path[-3:] == '.py':
            file_path = file_path[:-3] + '.json'  # replace .py with .json
        else:
            raise KeyError("Wrong file_path %s", file_path)

    # Callers may provide a source module path when requesting its localized text.
    if file_path.endswith('.pyc'):
        file_path = file_path[:-4] + '.json'
    elif file_path.endswith('.py'):
        file_path = file_path[:-3] + '.json'

    if func == '':
        # Auto-detect function based on call stack
        func = caller.function

    if lang == '':
        lang = config.language

    # Determine path to json text
    rel_path_list = _resolve_rel_path(caller, file_path, auto_detected)

    json_path = resource_path(os.path.join(INTL_CONTENT_PATH, lang, *rel_path_list))

    try:
        # browse json until text is found
        with open(json_path, encoding='utf-8') as f:
            text_dict = json.load(f)
            return _get_from_dict(text_dict, [func] + params)
    except (KeyError, FileNotFoundError):
        # If text not found in lang, try return English version
        if lang == 'en':
            raise KeyError(f'{[func] + params} not in {json_path} file')
        en_path = resource_path(os.path.join(INTL_CONTENT_PATH, 'en', *rel_path_list))
        try:
            with open(en_path, encoding='utf-8') as f:
                text_dict = json.load(f)
                return _get_from_dict(text_dict, [func] + params)
        except (KeyError, FileNotFoundError):
            raise KeyError(f'{[func] + params} not in {en_path} file')


def get_first_options(options: Mapping[str, Sequence[str]]) -> list[str]:
    '''
    Returns the first `option` in the values of the `options` dict.
    '''
    return list(map(lambda x: x[0], options.values()))


def closest_match(text: str, options: Iterable[str]) -> str:
    '''
    Finds the closest match to `text` in the `options_list`
    '''
    match = difflib.get_close_matches(text, options, n=1, cutoff=0.6)
    if len(match) == 0:
        raise ValidationError(f'{text} is not a valid language option')
    return match[0]


def fuzzy_reverse_dict_lookup(text: str, options: Mapping[str, Sequence[str]]) -> str:
    '''
    Returns the closest match to `text` out of the `options`
    :param text: The test string that needs to be found
    :param options: A dict with keys (the value that will be returned)
                    and values a list of the options to be matched against
    '''
    reverse_lookup_dict = {value: key for key, values in options.items() for value in values}
    match = closest_match(text, reverse_lookup_dict.keys())
    return reverse_lookup_dict[match]
