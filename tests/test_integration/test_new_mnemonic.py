import os
import pytest
from ethstaker_deposit.key_handling.key_derivation.mnemonic import abbreviate_words
from ethstaker_deposit.utils.constants import DEFAULT_VALIDATOR_KEYS_FOLDER_NAME
from ethstaker_deposit.utils.intl import load_text
from tests.shared_helpers import get_permissions, get_uuid
from tests.test_integration.helpers import build_shell_command, get_run_script_cmd
from tests.test_integration.interactive import InteractiveProcess


@pytest.mark.asyncio
async def test_script_abbreviated_mnemonic(deposit_cli_installed, cli_output_folder) -> None:
    my_folder_path = cli_output_folder

    cmd_args = [
        '--language', 'english',
        '--non_interactive',
        'new-mnemonic',
        '--num_validators', '5',
        '--mnemonic_language', 'english',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--folder', my_folder_path,
    ]
    cmd = build_shell_command(get_run_script_cmd(), *cmd_args)

    mnemonic_json_file = os.path.join(os.getcwd(), 'ethstaker_deposit/../ethstaker_deposit/cli/', 'new_mnemonic.json')
    msg_mnemonic_presentation = load_text(['msg_mnemonic_presentation'], mnemonic_json_file, 'new_mnemonic')
    msg_mnemonic_retype_prompt = load_text(['msg_mnemonic_retype_prompt'], mnemonic_json_file, 'new_mnemonic')
    msg_mnemonic_clipboard_warning = load_text(['msg_mnemonic_clipboard_warning'], mnemonic_json_file, 'new_mnemonic')

    seed_phrase = ''

    async with InteractiveProcess(cmd) as process:
        await process.expect(msg_mnemonic_presentation)

        # Collect the mnemonic itself, skipping the separator lines and the
        # clipboard warning printed around it.
        while True:
            line = await process.readline()
            if line is None:
                raise process.fail('Subprocess exited before asking to retype the mnemonic')
            if msg_mnemonic_retype_prompt in line:
                break
            if (
                not line.startswith('********************')
                and msg_mnemonic_clipboard_warning not in line
            ):
                seed_phrase += line

        assert len(seed_phrase.strip()) > 0
        # The CLI accepts abbreviated words as confirmation of a written down mnemonic.
        abbreviated_mnemonic = ' '.join(abbreviate_words(seed_phrase.strip().split(' ')))
        await process.sendline(abbreviated_mnemonic)
        await process.wait()

    # Check files
    validator_keys_folder_path = os.path.join(my_folder_path, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(validator_keys_folder_path))

    all_uuid = [
        get_uuid(validator_keys_folder_path + '/' + key_file)
        for key_file in key_files
        if key_file.startswith('keystore')
    ]
    assert len(set(all_uuid)) == 5

    # Verify file permissions
    if os.name == 'posix':
        for file_name in key_files:
            assert get_permissions(validator_keys_folder_path, file_name) == '0o400'
