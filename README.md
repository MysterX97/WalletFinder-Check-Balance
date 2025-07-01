# Multi-Chain Wallet Balance Scanner (Custom Word Permutations)

## Overview
This Python script is designed to generate mnemonic phrases from a custom word pool, derive cryptocurrency addresses across multiple chains (Ethereum, Bitcoin, Solana, Tron, Polygon, BNB Smart Chain), and then check for existing balances or transaction history on those addresses.
* **Finding a wallet with a balance using this method is practically impossible due to the astronomical number of combinations.** This script is intended purely for educational purposes and to demonstrate the process of mnemonic derivation and balance checking, not for finding "rich" wallets.
* **Web scraping is used for Ethereum/EVM balance checks (via Etherscan-like explorers).** This method is highly unreliable, prone to breaking due to website HTML changes, and may lead to your IP address being temporarily blocked by explorers due to rate limiting. Use with caution.
* Bitcoin (BTC) balances are checked via Blockstream.info API.
* Solana (SOL) balances are checked via Solana RPC API.
* Tron (TRX) and TRC-20 token balances are checked via Tronscan API.

## 🙏 Donations (Optional)

If you happen to discover a wallet with a balance using this tool, we kindly ask you to consider donating **1% of the found balance** to support the continued development of this open-source project.

Every contribution helps us improve, maintain, and extend this tool for the community. Thank you in advance for your support!

**Donation Wallet Addresses:**

- **BTC:**  
  `1CBmW7qzHnodZbw7QtGE3u6KX3ETYqJox7`

- **ETH:**  
  `0xbF2C788f4fBfF9d6D8CEB5D5d16C292e2d06d8Ff`

- **TRX / USDT (TRC20):**  
  `TZ3JULDC5Qj8iKyrh6qcW33Ju9jUs6kTap`

- **Polygon:**  
  `0xbF2C788f4fBfF9d6D8CEB5D5d16C292e2d06d8Ff`

- **BNB (BEP20):**  
  `0xbF2C788f4fBfF9d6D8CEB5D5d16C292e2d06d8Ff`


## Features
* **Custom Mnemonic Generation:** Generates 12-word mnemonic phrases by permuting words from a user-defined `WORD_POOL`.
* **Multi-Chain Address Derivation:** Derives addresses for:
    * Ethereum (EVM compatible, includes Polygon and BNB Smart Chain)
    * Bitcoin (BTC)
    * Solana (SOL)
    * Tron (TRX)
* **Balance & Transaction Checking:**
    * **Ethereum (EVM compatible chains like ETH, Polygon, BNB):** Scrapes Etherscan-like explorers for native ETH/MATIC/BNB balance, estimated USD value (if available on explorer), and transaction count.
    * **Bitcoin (BTC):** Uses Blockstream.info API to get native BTC balance and transaction count.
    * **Solana (SOL):** Uses Solana RPC API to get native SOL balance and check for transactions.
    * **Tron (TRX):** Uses Tronscan API to get native TRX balance and TRC-20 token balances (e.g., USDT TRC-20), and transaction count.
* **CoinGecko Price Integration:** Fetches current cryptocurrency prices (ETH, BTC, SOL, TRX, USDT, USDC, MATIC, BNB) from CoinGecko API to estimate USD value where direct scraping is not feasible or desired.
* **Results Logging:** Saves mnemonics, derived addresses, estimated USD value, and transaction status to `found_wallets.txt` if a balance above a threshold is found or if any transactions exist.
* **Configurable Parameters:** Easily adjust the `WORD_POOL`, `MNEMONIC_LENGTH`, and `MAX_ATTEMPTS_PER_RUN`.

## Prerequisites
Before running the script, ensure you have Python 3.8+ installed.

Install the necessary Python libraries:

```bash
pip install requests beautifulsoup4 eth-account mnemonic termcolor bip-utils
pip install aiohttp # For asyncio requests if you replace requests.get with aiohttp
