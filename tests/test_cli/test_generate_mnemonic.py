import os
import re
import pytest

from click.testing import CliRunner

from ethstaker_deposit.deposit import cli

from ethstaker_deposit.key_handling.key_derivation.mnemonic import (
    reconstruct_mnemonic,
)
from ethstaker_deposit.utils.constants import (
    MNEMONIC_LANG_OPTIONS,
    WORD_LISTS_PATH,
)

from tests.shared_helpers import clean_folder


@pytest.mark.parametrize(
    'language', MNEMONIC_LANG_OPTIONS.keys()
)
def test_normal_generate_mnemonic(language) -> None:
    # Test normal generate mnemonic workflow
    runner = CliRunner()
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'generate-mnemonic',
        '--mnemonic_language', language,
    ]
    result = runner.invoke(cli, arguments)

    assert result.exit_code == 0

    output_mnemonic = result.output.strip()

    assert reconstruct_mnemonic(output_mnemonic, WORD_LISTS_PATH, language) == output_mnemonic


@pytest.mark.parametrize(
    'language', MNEMONIC_LANG_OPTIONS.keys()
)
def test_generate_mnemonic_to_file(language) -> None:
    # Test generate mnemonic workflow that outputs the mnemonic into a file

    # Prepare output folder
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    output_file = os.path.join(my_folder_path, 'output')

    runner = CliRunner()
    arguments = [
        '--language', 'english',
        '--non_interactive',
        'generate-mnemonic',
        '--mnemonic_language', language,
        '--output_file', output_file,
    ]
    result = runner.invoke(cli, arguments)

    assert result.exit_code == 0

    assert os.path.exists(output_file)

    with open(output_file, encoding='utf-8') as f:
        output_mnemonic = f.read(2000).strip()

    assert reconstruct_mnemonic(output_mnemonic, WORD_LISTS_PATH, language) == output_mnemonic

    clean_folder(my_folder_path, my_folder_path, True)


@pytest.mark.parametrize(
    'language', MNEMONIC_LANG_OPTIONS.keys()
)
def test_generate_mnemonic_interactive(language) -> None:
    # Test normal generate mnemonic workflow
    runner = CliRunner()
    inputs = [language]
    data = '\n'.join(inputs)
    arguments = [
        '--language', 'english',
        '--ignore_connectivity',
        'generate-mnemonic',
    ]
    result = runner.invoke(cli, arguments, input=data)

    assert result.exit_code == 0

    re_match = re.search(
        r'This is your randomly generated mnemonic\:\n\n(?P<mnemonic>([^ ]+ ){23}[^ ]+)\n',
        result.output)

    assert (re_match is not None)

    output_mnemonic = re_match.group('mnemonic').strip()

    assert reconstruct_mnemonic(output_mnemonic, WORD_LISTS_PATH, language) == output_mnemonic
