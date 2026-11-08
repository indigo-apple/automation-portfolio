# Polymarket Liquidity Rewards Scanner

Lists Polymarket markets that pay **daily liquidity-provider rewards**, sorted by USD/day,
together with the qualifying max spread, minimum quote size and current liquidity.
Built for market makers hunting reward pools.

## What it does

- Reads Polymarket's public gamma API (no authentication).
- Extracts per-market reward configuration from `clobRewards` (daily rate, max spread, min size).
- Ranks markets by daily subsidy, so you can spot pools with high pay and low competition.

## Input

| Field | Default | Meaning |
|---|---|---|
| `minDailyRewardUsd` | `1` | Minimum daily reward pool (USD) |
| `maxSpreadCents` | unset | Only markets allowing a spread this tight or tighter |
| `minLiquidityUsd` | `0` | Minimum current liquidity |
| `pages` | `5` | Pages of 100 markets to scan |
| `topN` | `100` | Max rows |

## Output

| Field | Meaning |
|---|---|
| `question` | Market title |
| `daily_reward_usd` | Total daily LP reward pool |
| `rewards_max_spread_cents` | Max spread allowed to qualify (cents) |
| `rewards_min_size` | Minimum quote size to count |
| `liquidity_usd` | Current liquidity |
| `volume_24h_usd` | 24h volume |
| `end_date` | Market resolution date |
| `url` | Polymarket link |

## How much does it cost?

| Event | Price |
|---|---|
| `apify-default-dataset-item` (per result) | **$0.003** |
| `apify-actor-start` (per run) | **$0.005** |

A run returning 100 rewarded markets costs about **$0.31**.

## How to use it

1. Prefer markets with a high `daily_reward_usd` but low `liquidity_usd` — big subsidy, few competitors.
2. Quote both sides inside `rewards_max_spread_cents`, each side at least `rewards_min_size`.
3. Rewards are split pro-rata among qualifying quotes, so fewer quoters means a bigger share.
4. **Main risk:** adverse selection — getting filled by informed traders can wipe out the reward.

## Local run

```bash
python3 src/logic.py
```
