# builder

> **This command is for builders only, not validators.** It registers a builder deposit under [EIP-8282](https://eips.ethereum.org/EIPS/eip-8282) and has nothing to do with staking ETH or running a validator. If you want to generate validator keys and a deposit instead, use the **[new-mnemonic](new_mnemonic.md)** command.

{{#include ./snippet/warning_message.md}}

## Description
Generates builder keys and a builder deposit, per [EIP-8282](https://eips.ethereum.org/EIPS/eip-8282). A builder is a distinct role from a validator and is separate from the validator [deposit data file](deposit_data_file.md).

## Optional Arguments

- **`--mnemonic`**: An existing mnemonic to derive your builder keys from. If omitted, you will be asked whether you have one, or a new mnemonic will be generated for you. <span class="warning"></span>

- **`--mnemonic_password`**: The optional mnemonic password to use in your key generation. Only valid when reusing an existing mnemonic (`--mnemonic`). Note: It's not the keystore password. <span class="warning"></span>

- **`--mnemonic_language`**: The language of the BIP-39 mnemonic. Options are: 'chinese_simplified', 'chinese_traditional', 'czech', 'english', 'french', 'italian', 'japanese', 'korean', 'portuguese', 'spanish'.

- **`--builder_start_index`**: The index of the first builder's keys you wish to generate. If this is your first time generating builder keys with this mnemonic, use 0. If you have generated builder keys using this mnemonic before, use the next index from which you want to start generating keys from.

- **`--num_builders`**: Number of builders to create.

- **`--chain`**: The chain to use for generating the builder deposit data. Options are: 'mainnet', 'sepolia', 'hoodi', 'plataberget', 'ephemery', 'gnosis', or 'chiado'.

- **`--keystore_password`**: The password that is used to encrypt the provided keystore. Note: It's not your optional mnemonic password. <span class="warning"></span>

- **`--withdrawal_address`**: The Ethereum address that will be used as the builder's withdrawal address. It starts with '0x' followed by 40 hexadecimal characters. Please make sure you have full control over the address you choose here, either an EOA or a smart contract wallet. Do not choose an exchange wallet. This is **required** for builders, and cannot be changed once set on chain; it is also the sole authorization for a builder exit.

- **`--builder_amount`**: The amount to deposit to these builders in ether. Must be at least 1 ETH with no greater precision than 1 gwei. Unlike validator deposits, there is no protocol-defined maximum.

- **`--pbkdf2`**: Will use pbkdf2 key encryption instead of scrypt for generated keystore files as defined in [EIP-2335](https://eips.ethereum.org/EIPS/eip-2335#decryption-key). This can be a good alternative if you intend to work with a large number of keys, as it can improve performance. pbkdf2 encryption is, however, less secure than scrypt. You should only use this option if you understand the associated risks and have familiarity with encryption.

- **`--folder`**: The folder where keystore and builder deposit data files will be saved.

- **`--devnet_chain_setting`**: The custom chain setting of a devnet or testnet. Note that it will override your `--chain` choice. This should be a JSON string containing an object with the following keys: network_name, genesis_fork_version, exit_fork_version, genesis_validator_root, multiplier, min_activation_amount and min_deposit_amount.

## Output files
A successful call to this command will result in one or many [keystore files](keystore_file.md) created, one per builder, and one builder deposit data (`builder_deposit_data-*.json`) file created. This file follows the same structure as the [Deposit Data file](deposit_data_file.md), with two differences: `withdrawal_credentials` always uses the builder prefix (`0xb0`) followed by the withdrawal address, and `amount` has no protocol-defined maximum.

## Example Usage

```sh
./deposit builder
```

## Note

The withdrawal address **must** be under your control, either an EOA or a smart contract wallet. Do **not** use an exchange wallet. If you do not control the withdrawal address, the builder deposit **cannot** be recovered.

The newly generated mnemonic **must** be written down, on a piece of paper or transferred to steel. The application will attempt to clear the clipboard when this command finishes.
