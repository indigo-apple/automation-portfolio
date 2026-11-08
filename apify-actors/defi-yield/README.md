# DeFi Stablecoin Yield Scanner (DefiLlama)

Scans every DeFi lending and LP pool tracked by DefiLlama and returns stablecoin yields
filtered by TVL, APY, chain and impermanent-loss risk — with direct links to each pool.

## What it does

- Downloads the full DefiLlama pool dataset (15,000+ pools, refreshed hourly).
- Filters by minimum TVL, APY range, stablecoin flag and IL risk.
- Separates **base APY** (real lending/fee income) from **reward APY** (token subsidies).

## Input

| Field | Default | Meaning |
|---|---|---|
| `minTvlUsd` | `10000000` | Ignore pools smaller than this |
| `minApy` | `5` | Minimum APY (%) |
| `maxApy` | `200` | Maximum APY (%) — filters obvious scams |
| `stablecoinOnly` | `true` | Only stablecoin pools |
| `chains` | `[]` | Filter by chain, e.g. `Ethereum`, `Solana`, `Base` |
| `projects` | `[]` | Filter by project, e.g. `aave-v3`, `morpho-blue` |
| `excludeIl` | `true` | Exclude pools with impermanent-loss risk |
| `topN` | `100` | Max rows |

## Output

| Field | Meaning |
|---|---|
| `project` / `chain` / `symbol` | Protocol, chain, pool pair |
| `apy` | Total APY (base + reward) |
| `apy_base` | Sustainable portion |
| `apy_reward` | Subsidy portion (can drop to zero) |
| `tvl_usd` | Pool size |
| `url` | DefiLlama pool page |

## How much does it cost?

| Event | Price |
|---|---|
| `apify-default-dataset-item` (per result) | **$0.001** |
| `apify-actor-start` (per run) | **$0.005** |

A run returning 100 pools costs about **$0.11**.

## How to read the results

- `apy_base` is the real yield; `apy_reward` is a subsidy that can vanish overnight.
- Pools under ~$10M TVL are not worth the smart-contract risk regardless of APY.
- Data is sourced from DefiLlama and updated roughly hourly.

## Local run

```bash
python3 src/logic.py
```
