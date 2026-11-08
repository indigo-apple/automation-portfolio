#!/usr/bin/env python3
"""Demo 2 — 定时监控 + 阈值告警（可推 Telegram）

演示能力：状态去重、阈值判断、消息渲染、多渠道推送、失败不推进状态。
客户场景等价物：价格预警、库存告警、竞品上新提醒、服务器指标监控。

运行:
  python3 demo2_monitor.py                 # 只看会发什么，不真发
  python3 demo2_monitor.py --send          # 真推到 Telegram（需 env）
环境变量: TG_BOT_TOKEN / TG_CHAT_ID
"""
import csv
import glob
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
THRESHOLD_PCT = 0.01          # 费率超过 0.01% 就告警（演示用；生产按业务定）
STATE = os.path.join(HERE, "data", "alerted.txt")


def latest_csv():
    files = sorted(glob.glob(os.path.join(HERE, "data", "okx_funding_*.csv")))
    return files[-1] if files else None


def load_alerts(path):
    seen = set()
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            seen = {x.strip() for x in f}
    out, new = [], []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                rate = float(r["funding_rate_pct"] or 0)
            except ValueError:
                continue
            key = f"{r['instId']}:{r['next_funding_time']}"
            if abs(rate) >= THRESHOLD_PCT and key not in seen:
                out.append(r)
                new.append(key)
    return out, new


def render(alerts):
    lines = [f"⚠️ 资金费率异常 {len(alerts)} 个"]
    for r in alerts:
        lines.append(f"• {r['instId']}  {float(r['funding_rate_pct']):+.4f}%  "
                     f"({r['next_funding_time']})")
    return "\n".join(lines)


def send_tg(text):
    token = os.environ.get("TG_BOT_TOKEN")
    chat = os.environ.get("TG_CHAT_ID")
    if not token or not chat:
        raise SystemExit("缺少 TG_BOT_TOKEN / TG_CHAT_ID")
    body = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=body)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status == 200


def main():
    path = latest_csv()
    if not path:
        raise SystemExit("先跑 demo1_scraper.py 生成数据")
    alerts, new_keys = load_alerts(path)
    print(f"数据源: {os.path.basename(path)}  阈值 {THRESHOLD_PCT}%  命中 {len(alerts)}")
    if not alerts:
        print("无告警（静默）")
        return
    msg = render(alerts)
    print("\n--- 将要发送 ---\n" + msg + "\n---------------")
    if "--send" in sys.argv:
        if send_tg(msg):
            with open(STATE, "a", encoding="utf-8") as f:
                f.write("\n".join(new_keys) + "\n")
            print("已推送，状态已记录（下次相同告警不再重复）")
    else:
        print("（dry-run，加 --send 才真发）")


if __name__ == "__main__":
    main()
