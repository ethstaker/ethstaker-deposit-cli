# ethstaker-deposit-cli docs

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Documentation
- [Introduction](https://deposit-cli.ethstaker.cc/landing.html)
- [Quick Setup](https://deposit-cli.ethstaker.cc/quick_setup.html)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Introduction

`ethstaker-deposit-cli` is a tool for creating [EIP-2335 format](https://eips.ethereum.org/EIPS/eip-2335) BLS12-381 keystores and a corresponding `deposit_data*.json` file for [Ethereum Staking Launchpad](https://github.com/ethereum/staking-launchpad). One can also provide a keystore file to generate a `signed_exit_transaction*.json` file to be broadcast at a later date to exit a validator.

- **Warning: Please generate your keystores on your own safe, completely offline device.**
- **Warning: Please backup your mnemonic, keystores, and password securely.**

Please read [Launchpad Validator FAQs](https://launchpad.ethereum.org/faq#keys) before generating the keys.

You can find the audit report by Trail of Bits of the original staking-deposit-cli [here](https://github.com/trailofbits/publications/blob/master/reviews/ETH2DepositCLI.pdf). The audit of the updated ethstaker-deposit-cli is forthcoming.

