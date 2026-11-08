"""Polymarket 做市奖励池扫描 —— 找「每天有补贴、且没人满足报价条件」的市场。

数据源：gamma-api.polymarket.com（公开，无需鉴权）
奖励字段在 markets.clobRewards[] 里，每项有 rewardsDailyRate（USD/天）。
"""
import json
import urllib.parse
import urllib.request

BASE = "https://gamma-api.polymarket.com/markets"


def _as_list(value):
    """Gamma API returns arrays as JSON-encoded strings; expose real lists."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return [value]
    return value if isinstance(value, list) else []


def _as_floats(value):
    out = []
    for v in _as_list(value):
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            out.append(v)
    return out


UA = {"User-Agent": "Mozilla/5.0 polymarket-lp-scanner/1.0"}


def fetch_markets(pages=5, page_size=100):
    out = []
    for i in range(pages):
        q = urllib.parse.urlencode({
            "closed": "false", "active": "true",
            "limit": page_size, "offset": i * page_size,
            "order": "volume24hr", "ascending": "false",
        })
        req = urllib.request.Request(f"{BASE}?{q}", headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.loads(r.read())
        if not batch:
            break
        out.extend(batch)
        if len(batch) < page_size:
            break
    return out


def _daily_reward(m):
    total = 0.0
    for r in m.get("clobRewards") or []:
        try:
            total += float(r.get("rewardsDailyRate") or 0)
        except (TypeError, ValueError):
            continue
    return total


def scan(markets, min_daily=1.0, max_spread=None, min_liquidity=0.0, top=100):
    out = []
    for m in markets:
        daily = _daily_reward(m)
        if daily < min_daily:
            continue
        liq = float(m.get("liquidityNum") or m.get("liquidity") or 0)
        if liq < min_liquidity:
            continue
        spread = m.get("rewardsMaxSpread")
        if max_spread is not None and spread is not None and float(spread) > max_spread:
            continue
        out.append({
            "question": str(m.get("question") or ""),
            "slug": str(m.get("slug") or ""),
            "condition_id": str(m.get("conditionId") or ""),
            "daily_reward_usd": round(daily, 2),
            "rewards_min_size": m.get("rewardsMinSize"),
            "rewards_max_spread_cents": spread,
            "liquidity_usd": round(liq, 2),
            "volume_24h_usd": round(float(m.get("volume24hr") or 0), 2),
            "end_date": m.get("endDate"),
            "outcomes": _as_list(m.get("outcomes")),
            "outcome_prices": _as_floats(m.get("outcomePrices")),
            "url": f"https://polymarket.com/event/{m.get('slug')}",
        })
    out.sort(key=lambda x: -x["daily_reward_usd"])
    return out[:top]


if __name__ == "__main__":
    rows = scan(fetch_markets(pages=5), min_daily=1.0)
    print(f"命中 {len(rows)} 个有奖励池的市场")
    for r in rows[:10]:
        print(f"${r['daily_reward_usd']:>8.0f}/天  spread<={r['rewards_max_spread_cents']}c "
              f"min={r['rewards_min_size']}  liq={r['liquidity_usd']/1000:.0f}k  {r['question'][:55]}")
