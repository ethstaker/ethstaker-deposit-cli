import json
import os
import pytest
from ethstaker_deposit.key_handling.key_derivation.mnemonic import abbreviate_words
from ethstaker_deposit.utils.constants import DEFAULT_VALIDATOR_KEYS_FOLDER_NAME
from ethstaker_deposit.utils.intl import load_text
from tests.test_integration.helpers import build_shell_command, get_run_script_cmd, run_deposit_cli
from tests.test_integration.interactive import InteractiveProcess


@pytest.mark.asyncio
async def test_regeneration_across_processes(deposit_cli_installed, cli_output_folder) -> None:
    # Part 1: new-mnemonic through deposit.sh, capturing the generated mnemonic.
    folder_path_1 = os.path.join(cli_output_folder, 'new')
    folder_path_2 = os.path.join(cli_output_folder, 'existing')
    os.mkdir(folder_path_1)
    os.mkdir(folder_path_2)

    cmd_args = [
        '--language', 'english',
        '--non_interactive',
        'new-mnemonic',
        '--num_validators', '2',
        '--mnemonic_language', 'english',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--folder', folder_path_1,
    ]
    cmd = build_shell_command(get_run_script_cmd(), *cmd_args)

    mnemonic_json_file = os.path.join(os.getcwd(), 'ethstaker_deposit/../ethstaker_deposit/cli/', 'new_mnemonic.json')
    msg_mnemonic_presentation = load_text(['msg_mnemonic_presentation'], mnemonic_json_file, 'new_mnemonic')
    msg_mnemonic_retype_prompt = load_text(['msg_mnemonic_retype_prompt'], mnemonic_json_file, 'new_mnemonic')
    msg_mnemonic_clipboard_warning = load_text(['msg_mnemonic_clipboard_warning'], mnemonic_json_file, 'new_mnemonic')

    seed_phrase = ''
    async with InteractiveProcess(cmd) as process:
        await process.expect(msg_mnemonic_presentation)
        while True:
            line = await process.readline()
            if line is None:
                raise process.fail('Subprocess exited before asking to retype the mnemonic')
            if msg_mnemonic_retype_prompt in line:
                break
            if not line.startswith('********************') and msg_mnemonic_clipboard_warning not in line:
                seed_phrase += line
        assert len(seed_phrase.strip()) > 0
        # The CLI accepts abbreviated words as confirmation of a written down mnemonic.
        abbreviated_mnemonic = ' '.join(abbreviate_words(seed_phrase.strip().split(' ')))
        await process.sendline(abbreviated_mnemonic)
        await process.wait()

    validator_keys_folder_path_1 = os.path.join(folder_path_1, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    _, _, files_1 = next(os.walk(validator_keys_folder_path_1))
    part_1_key_files = sorted([key_file for key_file in files_1 if key_file.startswith('keystore')])
    assert len(part_1_key_files) == 2

    # Part 2: regenerate the same keys through deposit.sh in a second process.
    await run_deposit_cli(
        '--language', 'english',
        '--non_interactive',
        'existing-mnemonic',
        '--num_validators', '2',
        '--mnemonic', seed_phrase.strip(),
        '--validator_start_index', '0',
        '--chain', 'mainnet',
        '--keystore_password', 'MyPasswordIs',
        '--withdrawal_address', '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        '--folder', folder_path_2,
    )

    validator_keys_folder_path_2 = os.path.join(folder_path_2, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    _, _, files_2 = next(os.walk(validator_keys_folder_path_2))
    part_2_key_files = sorted([key_file for key_file in files_2 if key_file.startswith('keystore')])
    assert len(part_2_key_files) == 2

    # The same mnemonic must produce identical pubkeys/paths across processes.
    for key_file_1, key_file_2 in zip(part_1_key_files, part_2_key_files):
        with open(os.path.join(validator_keys_folder_path_1, key_file_1), encoding='utf-8') as f:
            keystore_1 = json.load(f)
        with open(os.path.join(validator_keys_folder_path_2, key_file_2), encoding='utf-8') as f:
            keystore_2 = json.load(f)
        assert keystore_1['pubkey'] == keystore_2['pubkey']
        assert keystore_1['path'] == keystore_2['path']
