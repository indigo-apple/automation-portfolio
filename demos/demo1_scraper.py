#!/usr/bin/env python3
"""Demo 1 — 网页/API 数据采集 → 结构化 CSV

演示能力：公开 API 抓取、并发请求、字段归一、落盘 CSV。
客户场景等价物：竞品价格监控、招聘岗位采集、房源/二手行情采集。

运行: python3 demo1_scraper.py
产物: data/okx_funding_YYYYmmdd_HHMM.csv
"""
import csv
import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

UA = {"User-Agent": "Mozilla/5.0 demo-scraper/1.0"}
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def fetch_top_swaps(limit=20):
    data = get("https://www.okx.com/api/v5/market/tickers?instType=SWAP")["data"]
    rows = []
    for d in data:
        try:
            rows.append((d["instId"], float(d.get("volCcy24h") or 0), float(d["last"])))
        except (KeyError, ValueError):
            continue
    rows.sort(key=lambda x: -x[1])
    return rows[:limit]


def fetch_funding(inst):
    try:
        d = get(f"https://www.okx.com/api/v5/public/funding-rate?instId={inst}")["data"][0]
        return {
            "instId": inst,
            "funding_rate_pct": round(float(d["fundingRate"]) * 100, 5),
            "next_funding_time": datetime.fromtimestamp(int(d["nextFundingTime"]) / 1000)
            .strftime("%Y-%m-%d %H:%M"),
        }
    except Exception as e:  # noqa: BLE001
        return {"instId": inst, "funding_rate_pct": None, "next_funding_time": str(e)[:40]}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()
    top = fetch_top_swaps(20)
    print(f"抓到 {len(top)} 个高成交合约，正在并发补充资金费率…")
    with ThreadPoolExecutor(max_workers=8) as ex:
        fees = {r["instId"]: r for r in ex.map(fetch_funding, [t[0] for t in top])}

    rows = []
    for inst, vol, last in top:
        f = fees.get(inst, {})
        rows.append({
            "instId": inst,
            "last_price": last,
            "volume_24h_usd": round(vol, 0),
            "funding_rate_pct": f.get("funding_rate_pct"),
            "next_funding_time": f.get("next_funding_time"),
        })

    path = os.path.join(OUT_DIR, f"okx_funding_{datetime.now():%Y%m%d_%H%M}.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    pos = [r for r in rows if (r["funding_rate_pct"] or 0) > 0]
    print(f"完成: {len(rows)} 行 / {time.time()-t0:.1f}s → {path}")
    print(f"其中 {len(pos)} 个为正费率（多头付空头），最高 {max(rows, key=lambda r: r['funding_rate_pct'] or -9)['instId']}")


if __name__ == "__main__":
    main()
