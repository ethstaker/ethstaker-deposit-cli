# Verify Mnemonic

{{#include ./snippet/warning_message.md}}

## Description

To verify a mnemonic you recorded, you can use the **[existing-mnemonic](existing_mnemonic.md)** command.

## Example Usage

Assume you have generated keys from index 0 with the **[new-mnemonic](new_mnemonic.md)** command, and these are in `./validator_keys`.

Generate one key, from the same index, using the  **[existing-mnemonic](existing_mnemonic.md)** command, and write the generated files into a separate directory. Then compare the `pubkey`. If it matches, you correctly recorded the mnemonic.

```sh
mkdir -p ./verification_key
./deposit --language english --non_interactive existing-mnemonic --withdrawal_address 0x0000000000000000000000000000000000000000 --chain mainnet --keystore_password WeWontUseThis --compounding --amount 2048 --num_validators 1 --validator_start_index 0 --folder ./verification_key
```

This creates one validator key as `keystore-m_12381_3600_0_0_0-<timestamp>.json` in the `./verification_key` directory. The command will prompt you for the mnemonic. The `deposit_data` file won't be used, so we can safely specify a dummy withdrawal address and amount.

Either just look at the two generated files, or use `jq` (install it first) to generate the pubkey from each:

```sh
jq .pubkey ./validator_keys/keystore-m_12381_3600_0_0_0-<timestamp>.json
jq .pubkey ./verification_key/keystore-m_12381_3600_0_0_0-<timestamp>.json
```

If this pubkey matches, the same mnemonic was used both times.
