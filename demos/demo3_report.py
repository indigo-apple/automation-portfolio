#!/usr/bin/env python3
"""Demo 3 — 自动生成 Excel 报表（带格式、汇总、条件高亮）

演示能力：读数据 → 清洗 → 生成可直接发给老板的 xlsx。
客户场景等价物：日报/月报、对账单、库存表、销售汇总。

运行: python3 demo3_report.py
产物: data/report_YYYYmmdd_HHMM.xlsx
依赖: openpyxl
"""
import csv
import glob
import os
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "data")
STRONG_PCT = 0.01          # |费率| >= 0.02% 视为强信号，高亮


def latest_csv():
    files = sorted(glob.glob(os.path.join(OUT_DIR, "okx_funding_*.csv")))
    if not files:
        raise SystemExit("先跑 demo1_scraper.py 生成数据")
    return files[-1]


def main():
    src = latest_csv()
    with open(src, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    wb = Workbook()
    ws = wb.active
    ws.title = "资金费率"

    headers = ["合约", "最新价", "24h成交额(USD)", "资金费率(%)", "方向", "下次结算"]
    ws.append(headers)

    head_fill = PatternFill("solid", fgColor="1E3A5F")
    thin = Side(style="thin", color="D9D9D9")
    border = Border(bottom=thin)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF", size=11)
        c.fill = head_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 24

    red = PatternFill("solid", fgColor="FFC7CE")     # 多头付费（费率为正）
    green = PatternFill("solid", fgColor="C6EFCE")   # 空头付费（费率为负）

    for i, r in enumerate(rows, start=2):
        rate = float(r["funding_rate_pct"] or 0)
        direction = "多头付费" if rate > 0 else ("空头付费" if rate < 0 else "持平")
        ws.append([
            r["instId"], float(r["last_price"]), float(r["volume_24h_usd"]),
            rate, direction, r["next_funding_time"],
        ])
        ws.cell(i, 2).number_format = "0.########"
        ws.cell(i, 3).number_format = "#,##0"
        ws.cell(i, 4).number_format = "0.0000"
        for c in ws[i]:
            c.border = border
        ws.cell(i, 4).alignment = Alignment(horizontal="right")
        ws.cell(i, 5).alignment = Alignment(horizontal="center")

        # 条件高亮：只给「费率单元格」上色，强信号加粗
        if abs(rate) >= STRONG_PCT:
            ws.cell(i, 4).fill = red if rate > 0 else green
            ws.cell(i, 4).font = Font(bold=True)

    last = ws.max_row
    total_row = last + 2
    ws.cell(total_row, 1, "汇总").font = Font(bold=True, size=11)
    ws.cell(total_row, 3, f"=SUM(C2:C{last})").number_format = "#,##0"
    ws.cell(total_row, 4, f"=AVERAGE(D2:D{last})").number_format = "0.0000"
    ws.cell(total_row, 5, f'=COUNTIF(E2:E{last},"多头付费")&" / "&COUNTIF(E2:E{last},"空头付费")')
    ws.cell(total_row, 6, "方向: 多 / 空")
    for c in ws[total_row]:
        c.font = Font(bold=True, size=11)

    widths = [20, 14, 20, 14, 12, 20]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:F{last}"

    # 打印设置：横向、缩到一页宽（保证导出的 PDF/图片不丢列）
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    out = os.path.join(OUT_DIR, f"report_{datetime.now():%Y%m%d_%H%M}.xlsx")
    wb.save(out)
    strong = sum(1 for r in rows if abs(float(r["funding_rate_pct"] or 0)) >= STRONG_PCT)
    print(f"已生成报表: {out}  ({len(rows)} 行，{strong} 个强信号已高亮)")


if __name__ == "__main__":
    main()
