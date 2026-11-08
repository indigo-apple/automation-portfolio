# Crypto Funding Rate Arbitrage Scanner

Scans perpetual futures funding rates across OKX, Gate.io, MEXC, HTX, KuCoin and Bitget, and returns cross-exchange funding-rate spreads ranked by annualized return. Find delta-neutral carry trades in seconds.

## 输入

见 `.actor/INPUT_SCHEMA.json`，所有项都有默认值，直接 Run 即可。

支持 8 家交易所：`okx` `gate` `mexc` `htx` `kucoin` `bitget` `binance` `bybit`。
**Binance / Bybit 对部分国家/地区的 IP 返回 451/403**，在 Apify 云端（欧美节点）可正常访问；
若某家失败，Actor 会在 SUMMARY 里记录错误，其余交易所照常输出。

## 输出

写入 Apify Dataset，字段：`base`, `long_exchange`, `short_exchange`, `long_rate_pct`, `short_rate_pct`, `spread_pct_per_period`, `apr_pct`, `funding_interval_h`, `next_funding_ts`


## 输出字段

| 字段 | 含义 |
|---|---|
| `base` | 币种（BTC / ETH / …） |
| `long_exchange` / `short_exchange` | 做多 / 做空的交易所 |
| `long_rate_pct` / `short_rate_pct` | 当前资金费率（每期，百分数） |
| `spread_pct_per_period` | 两家费率差（每期） |
| `apr_pct` | 年化价差收益（未扣手续费与滑点） |
| `funding_interval_h` | 结算周期（小时） |

## 怎么用

1. 在 `short_exchange` 开空、`long_exchange` 开多，两边仓位金额相等（delta 中性）
2. 每期结算收资金费，赚的是 `spread_pct_per_period`
3. **真实收益 = 年化价差 − 两边手续费（开平各一次）− 划转成本 − 滑点**
4. `apr_pct` 超过 200% 通常是流动性差的小币，先看盘口深度再动手

## 定价建议（Apify Console 设置）

- 按结果：`$0.002 / 条`（一次扫描 50 条 ≈ $0.10）
- 或按次：`$0.05 / run`


## 本地验证

```bash
python3 src/logic.py     # 不依赖 Apify SDK，直接打印结果
```

## 上架步骤

```bash
npm i -g apify-cli
apify login
cd funding-arb
apify push
```

然后在 Apify Console：
1. Actor → Publication → 填 README 的定价段
2. 类目选 `Crypto` / `Finance`
3. 设置 pay-per-result（见上面建议价）

数据源全部为公开 API，用户无需提供 key。
