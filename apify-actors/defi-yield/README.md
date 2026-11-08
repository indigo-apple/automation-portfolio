# DeFi Stablecoin Yield Scanner (DefiLlama)

Scans every DeFi lending/LP pool tracked by DefiLlama and returns stablecoin yields filtered by TVL, APY, chain and impermanent-loss risk. Output includes direct pool links.

## 输入

见 `.actor/INPUT_SCHEMA.json`，所有项都有默认值，直接 Run 即可。

## 输出

写入 Apify Dataset，字段：`project`, `chain`, `symbol`, `apy`, `apy_base`, `apy_reward`, `tvl_usd`, `stablecoin`, `il_risk`, `url`


## 输出字段

| 字段 | 含义 |
|---|---|
| `project` / `chain` / `symbol` | 协议 / 链 / 池子交易对 |
| `apy` | 总 APY（base + reward） |
| `apy_base` | 真实借贷/手续费收益（可持续部分） |
| `apy_reward` | 代币补贴（不可持续部分） |
| `tvl_usd` | 池子规模 |
| `url` | DefiLlama 池子详情 |

## 判断标准

- `apy_base` 才是真收益；`apy_reward` 是补贴，停了 APY 会断崖
- TVL < $10M 的池子 APY 再高也别重仓
- 数据源为 DefiLlama 公共 API，1-2 小时更新

## 定价建议

- 按结果：`$0.001 / 条`
- 或按次：`$0.02 / run`


## 本地验证

```bash
python3 src/logic.py     # 不依赖 Apify SDK，直接打印结果
```

## 上架步骤

```bash
npm i -g apify-cli
apify login
cd defi-yield
apify push
```

然后在 Apify Console：
1. Actor → Publication → 填 README 的定价段
2. 类目选 `Crypto` / `Finance`
3. 设置 pay-per-result（见上面建议价）

数据源全部为公开 API，用户无需提供 key。
