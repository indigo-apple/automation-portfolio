# Polymarket Liquidity Rewards Scanner

Lists Polymarket markets that pay daily liquidity-provider rewards, sorted by USD/day, with qualifying max spread, minimum size and current liquidity. Built for market makers hunting reward pools.

## 输入

见 `.actor/INPUT_SCHEMA.json`，所有项都有默认值，直接 Run 即可。

## 输出

写入 Apify Dataset，字段：`question`, `daily_reward_usd`, `rewards_max_spread_cents`, `rewards_min_size`, `liquidity_usd`, `volume_24h_usd`, `end_date`, `url`


## 输出字段

| 字段 | 含义 |
|---|---|
| `question` | 市场标题 |
| `daily_reward_usd` | 每天发放的做市奖励总额（USD） |
| `rewards_max_spread_cents` | 报价必须满足的最大点差（美分） |
| `rewards_min_size` | 报价最小股数（低于它不计奖励） |
| `liquidity_usd` | 当前流动性 |
| `url` | 市场链接 |

## 怎么用

1. 挑 `daily_reward_usd` 高、`liquidity_usd` 低的市场——补贴多、抢的人少
2. 在 `rewards_max_spread_cents` 之内双边挂单，每边 ≥ `rewards_min_size`
3. 奖励按你在合格报价中的占比分配，人越少分越多
4. **风险**：被扫单（adverse selection）会吃掉奖励

## 定价建议

- 按结果：`$0.003 / 条`
- 或按次：`$0.05 / run`


## 本地验证

```bash
python3 src/logic.py     # 不依赖 Apify SDK，直接打印结果
```

## 上架步骤

```bash
npm i -g apify-cli
apify login
cd polymarket-lp
apify push
```

然后在 Apify Console：
1. Actor → Publication → 填 README 的定价段
2. 类目选 `Crypto` / `Finance`
3. 设置 pay-per-result（见上面建议价）

数据源全部为公开 API，用户无需提供 key。
