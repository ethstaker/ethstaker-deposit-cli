# partial-deposit

{{#include ./snippet/warning_message.md}}

## Description
Creates a deposit file with an existing validator key. A validator key can be created using the **[new-mnemonic](new_mnemonic.md)** or the **[existing-mnemonic](existing_mnemonic.md)** commands. Can be used to initiate a validator or deposit to an existing validator.

If you wish to create a validator with legacy Type 0 (0x00) credentials, you must use `v1.3.0` of the software. Type 0 keys cannot be quantum-secure and will be sunset by the protocol in the coming years.

## Optional Arguments

- **`--chain`**: The chain to use for generating the deposit data. Options are: 'mainnet', 'sepolia', 'hoodi', 'ephemery', 'gnosis', or 'chiado'.

- **`--keystore`**: The keystore file associating with the validator you wish to deposit to.

- **`--keystore_password`**: The password that is used to encrypt the provided keystore. Note: It's not your optional mnemonic password. <span class="warning"></span>

- **`--amount`**: The amount to deposit per validator in ether. Must be at least the chain's minimum deposit amount (1 ETH on mainnet) with no greater precision than 1 gwei. Defaults to the chain's minimum activation amount (32 ETH on mainnet).

- **`--withdrawal_address`**: The withdrawal address of the existing validator or the desired withdrawal address.

- **`--compounding / --regular_withdrawal`**: Generates compounding Type 2 (0x02) validators with a 2048 ETH maximum effective balance by default, or regular withdrawal Type 1 (0x01) validators with a 32 ETH maximum effective balance if regular withdrawal is chosen. Defaults to compounding withdrawal.

- **`--output_folder`**: The folder path for the `deposit-*` JSON file.

- **`--devnet_chain_setting`**: The custom chain setting of a devnet or testnet. Note that it will override your `--chain` choice. This should be a JSON string containing an object with the following keys: network_name, genesis_fork_version, exit_fork_version, genesis_validator_root, multiplier, min_activation_amount and min_deposit_amount.

## Output file
A successful call to this command will result in one [deposit data file](deposit_data_file.md) created.

## Example Usage

```sh
./deposit partial-deposit --keystore /path/to/keystore.json
```
