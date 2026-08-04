import asyncio
import os

# For not importing ethstaker_deposit here
DEFAULT_VALIDATOR_KEYS_FOLDER_NAME = 'validator_keys'


async def main():
    my_folder_path = os.path.join(os.getcwd(), 'TESTING_TEMP_FOLDER')
    if not os.path.exists(my_folder_path):
        os.mkdir(my_folder_path)

    if os.name == 'nt':  # Windows
        run_script_cmd = 'bash deposit.sh'
    else:  # Mac or Linux
        run_script_cmd = './deposit.sh'

    install_cmd = run_script_cmd + ' install'
    print('[INFO] Creating subprocess 1: installation:', install_cmd)
    proc = await asyncio.create_subprocess_shell(
        install_cmd,
    )
    await asyncio.wait_for(proc.wait(), timeout=120)
    assert proc.returncode == 0
    print('[INFO] Installed')

    cmd_args = [
        run_script_cmd,
        '--language', 'english',
        '--non_interactive',
        'existing-mnemonic',
        '--num_validators', '1',
        '--mnemonic', '"abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"',
        '--mnemonic_password', 'TREZOR',
        '--validator_start_index', '1',
        '--chain', 'mainnet',
        '--keystore_password', 'TheirPassword',
        '--withdrawal_address', '""',
        '--folder', my_folder_path,
    ]
    proc = await asyncio.create_subprocess_shell(
        ' '.join(cmd_args),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for out in proc.stdout:
        print(out.decode('utf-8').rstrip())

    try:
        await asyncio.wait_for(proc.wait(), timeout=10)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise AssertionError('deposit-cli subprocess timed out')

    assert proc.returncode == 0

    # Check files
    validator_keys_folder_path = os.path.join(my_folder_path, DEFAULT_VALIDATOR_KEYS_FOLDER_NAME)
    _, _, key_files = next(os.walk(validator_keys_folder_path))

    # Clean up
    for key_file_name in key_files:
        os.remove(os.path.join(validator_keys_folder_path, key_file_name))
    os.rmdir(validator_keys_folder_path)
    os.rmdir(my_folder_path)


if os.name == 'nt':  # Windows
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
else:
    asyncio.run(main())
