import os
import pytest
from ethstaker_deposit.key_handling.key_derivation.mnemonic import (
    reconstruct_mnemonic,
)
from ethstaker_deposit.utils.constants import WORD_LISTS_PATH
from tests.test_integration.helpers import run_deposit_cli


@pytest.mark.asyncio
async def test_script(deposit_cli_installed, cli_output_folder) -> None:
    # Generate a mnemonic through deposit.sh and write it to a file.
    output_file = os.path.join(cli_output_folder, 'mnemonic.txt')

    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'generate-mnemonic',
        '--mnemonic_language', 'english',
        '--output_file', output_file,
    )

    assert os.path.exists(output_file)

    with open(output_file, encoding='utf-8') as f:
        output_mnemonic = f.read().strip()

    assert reconstruct_mnemonic(output_mnemonic, WORD_LISTS_PATH, 'english') == output_mnemonic
