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

## Translation Guidance

- Translate user-facing help, prompts, warnings, progress messages, success messages, and validation text naturally rather than word-for-word.
- Use the locale's normal terminology for “mnemonic” or “seed phrase”, but remain consistent within that locale.
- Keep Ethereum-specific proper nouns and standards terminology recognizable.
- Do not translate English mnemonic word-list language names when they are selectable values unless the existing locale convention already does so.
- For `pt-BR`, use Brazilian Portuguese rather than European Portuguese.
- For `zh-CN`, use Simplified Chinese.
- Preserve gender, politeness, and punctuation conventions appropriate to the target language.
- Use stable internal mnemonic-language keys as the default value in both generate-mnemonic and new-mnemonic locale files. Set each locale’s default to its corresponding key, such as english, french, italian, japanese, korean, portuguese, or chinese_simplified. Do not use translated display labels such as Français, Italiano, or 日本語; display labels belong only in prompts and choices. Preserve the English locale’s english default and leave unsupported mnemonic languages unchanged.

## Editing Workflow

- Select one locale directory at a time: `it`, `ar`, `el`, `fr`, `id`, `de`, `tr`, `ja`, `ko`, `ro`, `pt-BR`, `zh-CN`
- Compare its JSON leaves with the corresponding English JSON leaves.
- Translate only missing or English-fallback values.
- Inspect the exact current contents of each target JSON file before editing.
- Apply changes in small file-scoped patches rather than one large multi-file patch.
- Use stable JSON key paths as patch context; do not rely on indentation or large surrounding blocks.
- Preserve the file’s existing indentation and formatting. Do not reformat unrelated content.
- If a patch fails, do not retry the same patch unchanged. Re-read the affected file, locate the exact current key, and apply a smaller targeted patch.
- After each patch, verify that the intended keys changed and that no unrelated lines were modified.
- Do not count a translation as complete until the target value is confirmed to differ from the English source.
- Treat a failed patch as having made no changes unless verified otherwise.
- Validate that every English leaf key exists in the locale.
- Validate that each translated value contains exactly the same placeholders as its English source.
- Parse every edited JSON file.
- Run:

   ```bash
   python scripts/check_translations.py
   pytest -q tests/test_intl/test_json_schema.py
   ```

- Report the locale, files changed, keys translated, keys intentionally left unchanged as technical text, and any uncertain terminology requiring native-speaker review.

## Quality Bar

Do not use markers such as `[translated]`, machine-translation notes, or explanatory comments in JSON values. Do not silently leave English prose untranslated. If a reliable translation is not possible, stop and report the exact key rather than inventing a translation.
