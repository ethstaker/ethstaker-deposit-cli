# Translation Prompt

Translate every English fallback string in `ethstaker_deposit/intl/` into its locale's language.

## Role

Act as a professional software-localization translator with native-level fluency in the target language and strong familiarity with Ethereum validator tooling, BIP-39 mnemonics, keystores, withdrawal credentials, and Beacon Chain terminology.

## Scope

- Translate only values in locale JSON files under `ethstaker_deposit/intl/`.
- Use `ethstaker_deposit/intl/en/` as the source of truth for missing keys.
- Replace values that are identical to the English source, unless the value is intentionally a technical identifier or protocol term.
- Preserve all existing non-English translations unless correcting an obvious mistranslation.
- Do not change JSON keys, nesting, file names, command names, CLI flags, paths, filenames, or schema structure.

## Required Preservation

Keep these exactly unchanged wherever they occur:

- Python format placeholders such as `{min_deposit}`, `{activation_amount}`, and any future `{...}` placeholders.
- Newlines, tabs, and meaningful surrounding whitespace where they affect CLI formatting.
- Technical identifiers such as `BIP39`, `SignedBLSToExecutionChange`, `GENESIS_FORK_VERSION`, `GENESIS_VALIDATORS_ROOT`, `0x00`, `0x01`, `0x02`, `ETH`, `gwei`, `scrypt`, and `PBKDF2`.
- CLI flags, network names, JSON keys, directory names, and file patterns such as `keystore-*.json`.
- Security meaning, warnings, capitalization used for emphasis, and imperative tone.
- The key "arg_mnemonic_language": {
            "default": "english",


## Translation Guidance

- Translate user-facing help, prompts, warnings, progress messages, success messages, and validation text naturally rather than word-for-word.
- Use the locale's normal terminology for “mnemonic” or “seed phrase”, but remain consistent within that locale.
- Keep Ethereum-specific proper nouns and standards terminology recognizable.
- Do not translate English mnemonic word-list language names when they are selectable values unless the existing locale convention already does so.
- For `pt-BR`, use Brazilian Portuguese rather than European Portuguese.
- For `zh-CN`, use Simplified Chinese.
- Preserve gender, politeness, and punctuation conventions appropriate to the target language.

## Workflow

0. Already done: `it`
1. Select one locale directory at a time: `ar`, `el`, `fr`, `id`, `ja`, `ko`, `pt-BR`, `ro`, `tr`, or `zh-CN`.
2. Compare its JSON leaves with the corresponding English JSON leaves.
3. Translate only missing or English-fallback values.
4. Translate 40 placeholders and wait for the operator to prompt for another 40
4. Validate that every English leaf key exists in the locale.
5. Validate that each translated value contains exactly the same placeholders as its English source.
6. Parse every edited JSON file.
7. Run:

   ```bash
   python scripts/check_translations.py
   pytest -q tests/test_intl/test_json_schema.py
   ```

8. Report the locale, files changed, keys translated, keys intentionally left unchanged as technical text, and any uncertain terminology requiring native-speaker review.

## Quality Bar

Do not use markers such as `[translated]`, machine-translation notes, or explanatory comments in JSON values. Do not silently leave English prose untranslated. If a reliable translation is not possible, stop and report the exact key rather than inventing a translation.
