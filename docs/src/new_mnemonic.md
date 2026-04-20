# new-mnemonic

{{#include ./snippet/warning_message.md}}

## Description
Generates a new random BIP-39 mnemonic along with validator keystore and deposit files depending on how many validators you wish to create.

## Optional Arguments

- **`--mnemonic_language`**: The language of the BIP-39 mnemonic. Options are: 'chinese_simplified', 'chinese_traditional', 'czech', 'english', 'french', 'italian', 'japanese', 'korean', 'portuguese', 'spanish'.

- **`--chain`**: The chain to use for generating the deposit data. Options are: 'mainnet', 'sepolia', 'hoodi', 'ephemery', 'gnosis', or 'chiado'.

- **`--num_validators`**: Number of validators to create.

- **`--keystore_password`**: The password that is used to encrypt the provided keystore. Note: It's not your mnemonic password. <span class="warning"></span>

- **`--withdrawal_address`**: The Ethereum address that will be used in withdrawal. It typically starts with '0x' followed by 40 hexadecimal characters. Please make sure you have full control over the address you choose here. Once you set a withdrawal address on chain, it cannot be changed.

- **`--compounding / --regular-withdrawal`**: Generates compounding validators with 0x02 withdrawal credentials for a 2048 ETH maximum effective balance or generate regular validators with 0x01 withdrawal credentials for a 32 ETH maximum effective balance. Use of this option requires a withdrawal address. This feature is only supported on networks that have undergone the Pectra fork. Defaults to regular withdrawal.

- **`--amount`**: The amount to deposit per validator in ether. Only applies to compounding validators (0x02 withdrawal credentials). Must be at least the chain's minimum deposit amount (1 ETH on mainnet) with no greater precision than 1 gwei. Defaults to the chain's minimum activation amount (32 ETH on mainnet).

- **`--pbkdf2`**: Will use pbkdf2 key encryption instead of scrypt for generated keystore files as defined in [EIP-2335](https://eips.ethereum.org/EIPS/eip-2335#decryption-key). This can be a good alternative if you intend to work with a large number of keys, as it can improve performance. pbkdf2 encryption is, however, less secure than scrypt. You should only use this option if you understand the associated risks and have familiarity with encryption.

- **`--folder`**: The folder where keystore and deposit data files will be saved.

- **`--devnet_chain_setting`**: The custom chain setting of a devnet or testnet. Note that it will override your `--chain` choice. This should be a JSON string containing an object with the following keys: network_name, genesis_fork_version, exit_fork_version, genesis_validator_root, multiplier, min_activation_amount and min_deposit_amount.

## Output files
A successful call to this command will result in one or many [keystore files](keystore_file.md) created, one per validator created, and one [deposit data file](deposit_data_file.md) created. Non-compounding validators always deposit the chain's minimum activation amount (32 ETH on mainnet).

## Example Usage

```sh
./deposit new-mnemonic
```

## Note

The newly generated mnemonic **must** be written down, on a piece of paper or transferred to steel. The application will attempt to clear the clipboard when this command finishes. If the mnemonic is lost and the validator does not have a withdrawal address, funds **cannot** be recovered.

For non-compounding validators, a custom deposit amount requires an existing keystore file and the **[partial-deposit](partial_deposit.md)** command. Compounding validators (0x02 withdrawal credentials) can set a custom deposit amount directly using `--amount`.
