# ethstaker-deposit-cli docs

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
## Documentation
- [Introduction](https://deposit-cli.ethstaker.cc/landing.html)
- [Quick Setup](https://deposit-cli.ethstaker.cc/quick_setup.html)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Introduction

`ethstaker-deposit-cli` is a tool for creating [EIP-2335 format](https://eips.ethereum.org/EIPS/eip-2335) BLS12-381 keystores and a corresponding `deposit_data*.json` file for [Ethereum Staking Launchpad](https://github.com/ethereum/staking-launchpad) or the [Gnosis Beacon Chain deposit UI](https://github.com/gnosischain/gbc-deposit-ui/). One can also provide a keystore file to generate a `signed_exit_transaction*.json` file to be broadcast at a later date to exit a validator.

- **Warning: Please generate your keystores on your own safe, completely offline device.**
- **Warning: Please backup your mnemonic, keystores, and password securely.**

Please read [Launchpad Validator FAQs](https://launchpad.ethereum.org/faq#keys) before generating the keys.

The project has been through various security audits over the years. You can find them here:
- March 4, 2026: [Security assessment report by Trail of Bits](https://github.com/trailofbits/publications/blob/master/reviews/2026-03-ethstaker-deposit-cli-securityreview.pdf)
- December 13, 2024: [Security assessment report by Trail of Bits](https://github.com/trailofbits/publications/blob/master/reviews/2024-12-ethstaker-depositcli-securityreview.pdf)
- September 4, 2020: [Security assessment report by Trail of Bits](https://github.com/trailofbits/publications/blob/master/reviews/ETH2DepositCLI.pdf) of the original staking-deposit-cli project

## Canonical Deposit Contract and Launchpad

Ethstaker confirms the canonical Ethereum staking deposit contract addresses and launchpad URLs.
Please be sure that your ETH is deposited only to this deposit contract address, depending on chain.

Depositing to the wrong address **will** lose you your ETH.

- Ethereum mainnet
  - Deposit address: [0x00000000219ab540356cBB839Cbe05303d7705Fa](https://etherscan.io/address/0x00000000219ab540356cBB839Cbe05303d7705Fa)
  - [Launchpad](https://launchpad.ethereum.org/)
- Ethereum Hoodi testnet
  - Deposit address: [0x00000000219ab540356cBB839Cbe05303d7705Fa](https://hoodi.etherscan.io/address/0x00000000219ab540356cBB839Cbe05303d7705Fa)
  - [Launchpad](https://hoodi.launchpad.ethereum.org/)

- Gnosis mainnet
  - Deposit address: [0x0B98057eA310F4d31F2a452B414647007d1645d9](https://gnosis.blockscout.com/address/0x0B98057eA310F4d31F2a452B414647007d1645d9)
  - [Gnosis Beacon Chain deposit UI](https://deposit.gnosischain.com/)
- Chiado testnet
  - Deposit address: [0xb97036A26259B7147018913bD58a774cf91acf25](https://gnosis-chiado.blockscout.com/address/0xb97036A26259B7147018913bD58a774cf91acf25)
  - [Gnosis Beacon Chain deposit UI](https://deposit.gnosischain.com/)
