"""DeFi 稳定币收益扫描 —— 纯逻辑，数据源 DefiLlama 公共 API。"""
import json
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 defi-yield-scanner/1.0"}
POOLS_URL = "https://yields.llama.fi/pools"


def fetch_pools():
    req = urllib.request.Request(POOLS_URL, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["data"]


def scan(pools, min_tvl=10_000_000, min_apy=5.0, max_apy=200.0,
         stablecoin_only=True, chains=None, projects=None,
         exclude_il=True, top=100):
    chains = {c.lower() for c in chains} if chains else None
    projects = {p.lower() for p in projects} if projects else None
    out = []
    for p in pools:
        apy = p.get("apy") or 0
        tvl = p.get("tvlUsd") or 0
        if tvl < min_tvl or apy < min_apy or apy > max_apy:
            continue
        if stablecoin_only and not p.get("stablecoin"):
            continue
        if exclude_il and p.get("ilRisk") == "yes":
            continue
        if chains and (p.get("chain") or "").lower() not in chains:
            continue
        if projects and (p.get("project") or "").lower() not in projects:
            continue
        out.append({
            "pool_id": p.get("pool"),
            "project": p.get("project"),
            "chain": p.get("chain"),
            "symbol": p.get("symbol"),
            "apy": round(apy, 2),
            "apy_base": round(p.get("apyBase") or 0, 2),
            "apy_reward": round(p.get("apyReward") or 0, 2),
            "tvl_usd": int(tvl),
            "stablecoin": bool(p.get("stablecoin")),
            "il_risk": p.get("ilRisk"),
            "exposure": p.get("exposure"),
            "reward_tokens": p.get("rewardTokens") or [],
            "url": f"https://defillama.com/yields/pool/{p.get('pool')}",
        })
    out.sort(key=lambda x: -x["apy"])
    return out[:top]


if __name__ == "__main__":
    rows = scan(fetch_pools(), min_tvl=20_000_000, min_apy=8)
    print(f"命中 {len(rows)} 个池子")
    for r in rows[:10]:
        print(f"{r['apy']:6.2f}%  {r['project'][:18]:18s} {r['chain'][:8]:8s} {r['symbol'][:20]:20s} "
              f"TVL {r['tvl_usd']/1e6:.0f}M")
