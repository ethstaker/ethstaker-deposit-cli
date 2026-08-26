# existing-mnemonic

{{#include ./snippet/warning_message.md}}

## Description
Uses an existing BIP-39 mnemonic phrase for key generation.

## Optional Arguments

- **`--chain`**: The chain to use for generating the deposit data. Options are: 'mainnet', 'sepolia', 'hoodi', 'plataberget', 'ephemery', 'gnosis', or 'chiado'.

- **`--mnemonic`**: The mnemonic to use to create validator keys. <span class="warning"></span>

- **`--mnemonic_language`**: The language of your mnemonic. If this is not provided we will attempt to determine it based on the mnemonic.

- **`--mnemonic_password`**: The optional mnemonic password to use in your key generation. Generally **not** provided, be sure you understand its use. Note: It's not the keystore password. <span class="warning"></span>

- **`--validator_start_index`**: The index of the first validator's keys you wish to generate. If this is your first time generating keys with this mnemonic, use 0. If you have generated keys using this mnemonic before, use the next index from which you want to start generating keys from. As an example if you've generated 4 keys before (keys #0, #1, #2, #3), then enter 4 here.

- **`--num_validators`**: Number of validators to create.

- **`--keystore_password`**: The password that is used to encrypt the provided keystore. Note: It's not your optional mnemonic password. <span class="warning"></span>

- **`--withdrawal_address`**: The Ethereum address that will be used in withdrawal. It starts with '0x' followed by 40 hexadecimal characters. Please make sure you have full control over the address you choose here, either an EOA or a smart contract wallet. Do not choose an exchange wallet. Once you set a withdrawal address on chain, it cannot be changed.

- **`--compounding / --regular_withdrawal`**: Generates compounding Type 2 (0x02) validators with a 2048 ETH maximum effective balance by default, or regular withdrawal Type 1 (0x01) validators with a 32 ETH maximum effective balance if regular withdrawal is chosen. Defaults to compounding withdrawal.

- **`--amount`**: The amount to deposit per validator in ether. Only applies to compounding validators (0x02 withdrawal credentials). Must be at least the chain's minimum deposit amount (1 ETH on mainnet) with no greater precision than 1 gwei. Defaults to the chain's minimum activation amount (32 ETH on mainnet).

- **`--pbkdf2`**: Will use pbkdf2 key derivation instead of scrypt for generated keystore files as defined in [EIP-2335](https://eips.ethereum.org/EIPS/eip-2335#decryption-key). This can be a good alternative if you intend to work with a large number of keys, as it can improve performance however it is less secure. You should only use this option if you understand the associated risks and have familiarity with encryption.

- **`--folder`**: The folder where keystore and deposit data files will be saved.

- **`--devnet_chain_setting`**: The custom chain setting of a devnet or testnet. Note that it will override your `--chain` choice. This should be a JSON string containing an object with the following keys: network_name, genesis_fork_version, exit_fork_version, genesis_validator_root, multiplier, min_activation_amount and min_deposit_amount.

## Output files
A successful call to this command will result in one or many [keystore files](keystore_file.md) created, one per validator created, and one [deposit data file](deposit_data_file.md) created. Non-compounding validators always deposit the chain's minimum activation amount (32 ETH on mainnet).

## Example Usage

```sh
./deposit existing-mnemonic
```

## Note

The withdrawal address **must** be under your control, either an EOA or a smart contract wallet. Do **not** use an exchange wallet. If you do not control the withdrawal address, funds **cannot** be recovered.

For non-compounding validators, a custom deposit amount requires an existing keystore file and the **[partial-deposit](partial_deposit.md)** command. Compounding validators (0x02 withdrawal credentials) can set a custom deposit amount directly using `--amount`.
