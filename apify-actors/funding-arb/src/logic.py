"""资金费率套利扫描器 —— 纯逻辑，不依赖 Apify SDK，可单独跑。"""
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 funding-arb-scanner/1.0"}
TIMEOUT = 25

# exchange -> 每 8 小时结算一次（Gate/MEXC/HTX/KuCoin/OKX 目前都是 8h）
FUNDING_INTERVAL_HOURS = {
    "okx": 8, "gate": 8, "mexc": 8, "htx": 8, "kucoin": 8, "bitget": 8,
    "binance": 8, "bybit": 8,
}

ALIAS = {"XBT": "BTC", "XBTUSD": "BTC"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())


def normalize(symbol):
    s = str(symbol).upper().strip()
    for suf in ("-USDT-SWAP", "USDT-SWAP", "-USDTM", "USDTM", "-USDT", "_USDT", "USDT", "-PERP", "PERP"):
        if s.endswith(suf) and len(s) > len(suf):
            s = s[: -len(suf)]
            break
    s = s.strip("-_")
    s = ALIAS.get(s, s)
    # 过滤掉带数字的合成合约（如 CSOPSAMSUNG2L）
    if not s or not re.fullmatch(r"[A-Z]{2,10}", s):
        return None
    return s


# ---------------- 各交易所抓取 ----------------

def fetch_okx(limit=120):
    tickers = _get("https://www.okx.com/api/v5/market/tickers?instType=SWAP").get("data", [])
    rows = []
    for t in tickers:
        try:
            rows.append((t["instId"], float(t.get("volCcy24h") or 0)))
        except Exception:  # noqa: BLE001
            continue
    rows.sort(key=lambda x: -x[1])
    ids = [r[0] for r in rows[:limit]]

    def one(inst):
        try:
            d = _get(f"https://www.okx.com/api/v5/public/funding-rate?instId={inst}")["data"][0]
            return ("okx", inst, float(d["fundingRate"]), int(d.get("nextFundingTime") or 0))
        except Exception:  # noqa: BLE001
            return None

    with ThreadPoolExecutor(max_workers=12) as ex:
        return [r for r in ex.map(one, ids) if r]


def fetch_gate():
    out = []
    for d in _get("https://api.gateio.ws/api/v4/futures/usdt/tickers"):
        try:
            out.append(("gate", d["contract"], float(d["funding_rate"]), 0))
        except Exception:  # noqa: BLE001
            continue
    return out


def fetch_mexc():
    out = []
    for d in _get("https://contract.mexc.com/api/v1/contract/ticker").get("data", []):
        try:
            out.append(("mexc", d["symbol"], float(d["fundingRate"]), 0))
        except Exception:  # noqa: BLE001
            continue
    return out


def fetch_htx():
    out = []
    for d in _get("https://api.hbdm.com/linear-swap-api/v1/swap_batch_funding_rate").get("data", []):
        try:
            out.append(("htx", d["contract_code"], float(d["funding_rate"]), int(d.get("funding_time") or 0)))
        except Exception:  # noqa: BLE001
            continue
    return out


def fetch_kucoin():
    out = []
    for d in _get("https://api-futures.kucoin.com/api/v1/contracts/active").get("data", []):
        try:
            out.append(("kucoin", d["symbol"], float(d["fundingFeeRate"]), int(d.get("nextFundingRateDateTime") or 0)))
        except Exception:  # noqa: BLE001
            continue
    return out


def fetch_bitget():
    out = []
    for d in _get("https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES").get("data", []):
        try:
            out.append(("bitget", d["symbol"], float(d["fundingRate"]), 0))
        except Exception:  # noqa: BLE001
            continue
    return out


def fetch_binance():
    """Binance USDT-M 永续资金费率（需非限制地区 IP，Apify 云端可正常访问）。"""
    data = _get("https://fapi.binance.com/fapi/v1/premiumIndex")
    if not isinstance(data, list):
        raise RuntimeError(f"binance 返回异常: {str(data)[:120]}")
    out = []
    for d in data:
        try:
            out.append(("binance", d["symbol"], float(d["lastFundingRate"]),
                        int(d.get("nextFundingTime") or 0)))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def fetch_bybit():
    """Bybit 线性永续资金费率（需非限制地区 IP）。"""
    data = _get("https://api.bybit.com/v5/market/tickers?category=linear")
    items = (data or {}).get("result", {}).get("list") if isinstance(data, dict) else None
    if not items:
        raise RuntimeError(f"bybit 返回异常: {str(data)[:120]}")
    out = []
    for d in items:
        try:
            out.append(("bybit", d["symbol"], float(d["fundingRate"]),
                        int(d.get("nextFundingTime") or 0)))
        except (KeyError, TypeError, ValueError):
            continue
    return out


FETCHERS = {
    "okx": fetch_okx,
    "gate": fetch_gate,
    "mexc": fetch_mexc,
    "htx": fetch_htx,
    "kucoin": fetch_kucoin,
    "bitget": fetch_bitget,
    "binance": fetch_binance,
    "bybit": fetch_bybit,
}


def collect(exchanges):
    """返回 {base: {exchange: (symbol, rate, next_ts)}}，单家失败不影响整体。"""
    book, errors = {}, {}
    for ex in exchanges:
        fn = FETCHERS.get(ex)
        if not fn:
            continue
        try:
            rows = fn()
        except Exception as e:  # noqa: BLE001
            errors[ex] = f"{type(e).__name__}: {e}"[:150]
            continue
        for exch, sym, rate, nxt in rows:
            base = normalize(sym)
            if not base:
                continue
            slot = book.setdefault(base, {})
            # 同一 base 同家只留绝对值更大的那个（避免重复合约）
            if exch not in slot or abs(rate) > abs(slot[exch][1]):
                slot[exch] = (sym, rate, nxt)
    return book, errors


def scan(exchanges, min_apr=10.0, min_liquidity_pairs=2, top=50, max_abs_rate_pct=0.5):
    book, errors = collect(exchanges)
    out = []
    for base, slot in book.items():
        if len(slot) < min_liquidity_pairs:
            continue
        items = sorted(slot.items(), key=lambda kv: kv[1][1])
        low_ex, (low_sym, low_rate, _) = items[0]
        high_ex, (high_sym, high_rate, high_ts) = items[-1]
        if high_ex == low_ex or high_rate <= low_rate:
            continue
        # 单期费率超过 max_abs_rate_pct 基本是流动性差/数据陈旧，直接丢弃
        if max(abs(high_rate), abs(low_rate)) * 100 > max_abs_rate_pct:
            continue
        hours = max(FUNDING_INTERVAL_HOURS.get(high_ex, 8), FUNDING_INTERVAL_HOURS.get(low_ex, 8))
        periods_per_year = 24 / hours * 365
        spread = high_rate - low_rate
        apr = spread * periods_per_year * 100
        if apr < min_apr:
            continue
        out.append({
            "base": base,
            "long_exchange": low_ex, "long_symbol": low_sym,
            "short_exchange": high_ex, "short_symbol": high_sym,
            "long_rate_pct": round(low_rate * 100, 5),
            "short_rate_pct": round(high_rate * 100, 5),
            "spread_pct_per_period": round(spread * 100, 5),
            "funding_interval_h": hours,
            "apr_pct": round(apr, 2),
            "next_funding_ts": high_ts,
        })
    out.sort(key=lambda x: -x["apr_pct"])
    return out[:top], errors, len(book)


if __name__ == "__main__":
    import sys
    exs = sys.argv[1].split(",") if len(sys.argv) > 1 else ["okx", "gate", "mexc", "htx", "kucoin"]
    rows, errs, n = scan(exs, min_apr=10)
    print(f"覆盖 {n} 个币种，命中 {len(rows)} 个套利机会；失败: {errs}")
    for r in rows[:10]:
        print(f"{r['base']:6s} 空{r['short_exchange']:7s}({r['short_rate_pct']:+.4f}%) "
              f"/ 多{r['long_exchange']:7s}({r['long_rate_pct']:+.4f}%)  APR {r['apr_pct']:.1f}%")
