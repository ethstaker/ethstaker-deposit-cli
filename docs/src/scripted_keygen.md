# Fully Automatic Key Generation

{{#include ./snippet/warning_message.md}}

## Description

ethstaker-deposit-cli supports generating keys via script, and no prompts will be shown. This is achieved by using the **[generate-mnemonic](generate_mnemonic.md)** command followed by the **[existing-mnemonic](existing_mnemonic.md)** command. Of necessity, the keystore password and mnemonic will be on command line with this workflow. Ensure these secrets are properly safeguarded.

Parameters are positional: `--language`, `--non-interactive`, `--ignore_connectivity` all come before the command.

## Example Usage

```sh
./deposit --non_interactive --ignore_connectivity --language english generate-mnemonic --mnemonic_language english --output_file ./test-mnemonic.txt
```

This creates a file `./test-mnemonic.txt`, which is used in the following step. Fill in the `<>` placeholders. If creating validators for the first time with this mnemonic, choose a start index of `0`.

```sh
./deposit --non_interactive --ignore_connectivity --language english existing-mnemonic --compounding --amount <deposit-amount> --withdrawal_address <your-withdrawal-address> --chain mainnet --keystore_password <your-password> --num_validators <num-validators-to-create> --validator_start_index <index-to-start> --mnemonic "$(cat ./test-mnemonic.txt)"
```

This creates the desired number of validator keys as `keystore-m_12381_3600_<index>_0_0-<timestamp>.json` and a matching `deposit_data-<timestamp>.json` in the `./validator_keys` directory. Add a `--folder` parameter to adjust the location of the output files.

## Note

The withdrawal address **must** be under your control, either an EOA or a smart contract wallet. Do **not** use an exchange wallet. If you do not control the withdrawal address, funds **cannot** be recovered.

The newly generated mnemonic **must** be written down, on a piece of paper or transferred to steel. If the mnemonic is lost and the validator does not have a withdrawal address, funds **cannot** be recovered.

For non-compounding validators, a custom deposit amount requires an existing keystore file and the **[partial-deposit](partial_deposit.md)** command. Compounding validators (0x02 withdrawal credentials) can set a custom deposit amount directly using `--amount`.
