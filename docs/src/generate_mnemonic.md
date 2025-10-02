# generate-mnemonic

{{#include ./snippet/warning_message.md}}

## Description

Generates a new random BIP-39 mnemonic. If you also want to create your validator keystore and deposit files, you should be using the **[new-mnemonic](new_mnemonic.md)**
or the **[existing-mnemonic](existing_mnemonic.md)** command instead. This command can be used as part of some automation where you can first generate your mnemonic with
`generate-mnemonic` and generate the validator keystore and deposit files with `existing-mnemonic` without any interactive prompt.

## Optional Arguments

- **`--mnemonic_language`**: The language of the BIP-39 mnemonic. Options are: 'chinese_simplified', 'chinese_traditional', 'czech', 'english', 'french', 'italian', 'japanese', 'korean', 'portuguese', 'spanish'.

- **`--output_file`**: An optional file path where to write the mnemonic. When used, it will write the mnemonic to the file instead of displaying the mnemonic.

## Output

By default, it will output the mnemonic on the standard output, in your terminal. You can decide to output this in a file instead using the **`--output_file`** optional argument.

## Example Usage

```sh
./deposit generate-mnemonic
```

## Note

The newly generated mnemonic **must** be written down, on a piece of paper or transferred to steel. If the mnemonic is lost and the validator does not have a withdrawal address, funds **cannot** be recovered.
