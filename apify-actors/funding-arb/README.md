# Crypto Funding Rate Arbitrage Scanner

Scans perpetual-futures funding rates across **8 exchanges** and returns cross-exchange
spreads ranked by annualized return, so you can find delta-neutral carry trades in seconds.

Supported exchanges: `okx` `gate` `mexc` `htx` `kucoin` `bitget` `binance` `bybit`
(all public APIs — no API keys required).

## What it does

1. Pulls every USDT-margined perpetual contract from each selected exchange.
2. Normalizes inconsistent symbol formats (`BTC-USDT-SWAP`, `XBTUSDTM`, `BTC_USDT` → `BTC`).
3. Converts each funding rate into an annualized number using the venue's settlement interval.
4. Pairs up venues and ranks the spread: **short on the high-rate venue, long on the low-rate venue**.
5. Drops illiquid/stale contracts whose per-period rate is implausibly large.

## Input

All fields have defaults — press **Start** and it runs.

| Field | Default | Meaning |
|---|---|---|
| `exchanges` | all 8 | Venues to scan |
| `minAprPct` | `10` | Only return spreads above this annualized % |
| `maxAbsRatePct` | `0.5` | Discard contracts with a per-period rate above this (illiquid filter) |
| `topN` | `50` | Max rows in the dataset |

> **Note on Binance / Bybit:** they block some regions with HTTP 451/403. On Apify cloud
> (US/EU egress) they work. If one venue fails, it is recorded in the run summary and the
> remaining venues still return results.

## Output

One dataset item per opportunity:

| Field | Meaning |
|---|---|
| `base` | Coin (BTC, ETH, …) |
| `long_exchange` / `short_exchange` | Where to go long / short |
| `long_rate_pct` / `short_rate_pct` | Current funding rate per settlement period |
| `spread_pct_per_period` | Difference between the two rates |
| `apr_pct` | Annualized spread (before fees and slippage) |
| `funding_interval_h` | Settlement interval in hours |

## How much does it cost?

Pay-per-event. You only pay for the results you actually get.

| Event | Price |
|---|---|
| `apify-default-dataset-item` (per result) | **$0.002** |
| `apify-actor-start` (per run) | **$0.005** |

A typical run returning 50 ranked pairs costs about **$0.11**. Small runs are cheaper —
a run with 10 results costs about $0.03.

## How to use the results

1. Open a short on `short_exchange` and a long of equal notional on `long_exchange`.
2. Collect the funding payment each settlement while the spread holds.
3. **Real return = annualized spread − trading fees (open + close on both legs) − transfer costs − slippage.**
4. An `apr_pct` above ~200% is usually an illiquid micro-cap. Check order-book depth before sizing.

## Notes

- Not financial advice. Funding rates change continuously; always re-check before entering.
- Data comes from public exchange endpoints and is not guaranteed to be real-time or complete.

## Local run (no Apify account)

```bash
python3 src/logic.py
```
