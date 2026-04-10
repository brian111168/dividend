"""
report.py
根據配息資料產生美化 HTML 報表字串（供 Streamlit 嵌入或 PDF 匯出用）
"""
from __future__ import annotations
import pandas as pd
from datetime import datetime


# ── 配色系統（保持不變） ──────────────────────────────────────
CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@300;400;500&family=Noto+Sans+TC:wght@300;400;500&display=swap');

  :root {
    --cream:        #faf9f7;
    --white:        #ffffff;
    --stone-light:  #f0ede8;
    --stone:        #e0dbd3;
    --border:       #ccc9c2;
    --ink:          #2c2c2a;
    --ink-muted:    #5f5e5a;
    --ink-faint:    #9a9790;
    --sage-dark:    #4a6b4d;
    --sage:         #7a9e7d;
    --sage-light:   #c8dac9;
    --sage-pale:    #edf4ee;
    --gold-dark:    #7a6840;
    --gold:         #b8a87a;
    --gold-light:   #e8dfc8;
    --gold-pale:    #faf6ec;
    --radius:       8px;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Noto Sans TC', 'Helvetica Neue', sans-serif;
    background: var(--cream);
    color: var(--ink);
    padding: 2.5rem 2rem;
  }

  .report-wrap {
    max-width: 960px;
    margin: 0 auto;
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 32px rgba(44,44,42,0.08);
  }

  .report-head {
    background: var(--ink);
    padding: 2rem 2.5rem 1.8rem;
    position: relative;
  }

  .report-head::after {
    content: '';
    display: block;
    width: 48px;
    height: 2px;
    background: var(--gold);
    margin-top: 1rem;
  }

  .report-title {
    font-family: 'Noto Serif TC', serif;
    font-size: 1.5rem;
    font-weight: 400;
    color: #ffffff;
    letter-spacing: 0.1em;
  }

  .report-subtitle {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.45);
    letter-spacing: 0.15em;
    margin-top: 0.3rem;
    text-transform: uppercase;
  }

  .report-meta {
    position: absolute;
    top: 2rem;
    right: 2.5rem;
    text-align: right;
    font-size: 0.72rem;
    color: rgba(255,255,255,0.4);
    line-height: 1.7;
    letter-spacing: 0.06em;
  }

  .summary-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0;
    border-bottom: 1px solid var(--border);
  }

  .summary-card {
    padding: 1.2rem 1.5rem;
    border-right: 1px solid var(--border);
  }

  .summary-card:last-child { border-right: none; }

  .s-label {
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    color: var(--ink-faint);
    text-transform: uppercase;
    margin-bottom: 0.4rem;
  }

  .s-value {
    font-size: 1.5rem;
    font-weight: 300;
    color: var(--ink);
    letter-spacing: -0.01em;
    font-family: 'Noto Serif TC', serif;
  }

  .s-unit {
    font-size: 0.72rem;
    color: var(--ink-faint);
    margin-left: 3px;
    font-family: 'Noto Sans TC', sans-serif;
  }

  .stock-block { border-bottom: 1px solid var(--border); }
  .stock-block:last-child { border-bottom: none; }

  .stock-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem 0.8rem;
    background: var(--stone-light);
    border-bottom: 1px solid var(--border);
  }

  .stock-badge {
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--ink);
    letter-spacing: 0.05em;
  }

  .stock-name {
    font-size: 0.8rem;
    color: var(--ink-muted);
  }

  .stock-count {
    margin-left: auto;
    font-size: 0.72rem;
    color: var(--ink-faint);
    background: var(--stone);
    padding: 3px 10px;
    border-radius: 20px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
  }

  thead tr {
    background: var(--white);
    border-bottom: 1px solid var(--border);
  }

  thead th {
    padding: 0.65rem 1.2rem;
    text-align: left;
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    color: var(--ink-faint);
    text-transform: uppercase;
    font-weight: 400;
  }

  thead th:not(:first-child) { text-align: right; }

  tbody tr {
    border-bottom: 1px solid var(--stone);
    transition: background 0.12s;
  }

  tbody tr:last-child { border-bottom: none; }
  tbody tr:hover { background: var(--stone-light); }

  tbody td {
    padding: 0.7rem 1.2rem;
    color: var(--ink);
  }

  tbody td:not(:first-child) { text-align: right; }

  .num-zero { color: var(--ink-faint); }

  .subtotal-row {
    background: var(--gold-pale) !important;
    border-top: 1px solid var(--gold-light) !important;
    border-bottom: 2px solid var(--gold-light) !important;
  }

  .subtotal-row td {
    color: var(--gold-dark) !important;
    font-weight: 500;
    font-size: 0.82rem;
    padding: 0.6rem 1.2rem;
  }

  .total-section {
    background: var(--sage-dark);
    padding: 1rem 1.5rem;
    display: grid;
    grid-template-columns: 1fr repeat(3, 120px);
    align-items: center;
    gap: 0;
  }

  .total-label {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.6);
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  .total-value {
    text-align: right;
    font-size: 1rem;
    font-weight: 400;
    color: #ffffff;
    font-family: 'Noto Serif TC', serif;
  }

  .total-value .unit {
    font-size: 0.7rem;
    color: rgba(255,255,255,0.5);
    margin-left: 2px;
  }

  .badge {
    display: inline-block;
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 3px;
    letter-spacing: 0.06em;
  }

  .badge-cash {
    background: var(--sage-pale);
    color: var(--sage-dark);
    border: 1px solid var(--sage-light);
  }

  .badge-both {
    background: var(--gold-pale);
    color: var(--gold-dark);
    border: 1px solid var(--gold-light);
  }

  .report-foot {
    padding: 1rem 1.5rem;
    background: var(--stone-light);
    border-top: 1px solid var(--border);
    font-size: 0.7rem;
    color: var(--ink-faint);
    display: flex;
    justify-content: space-between;
    letter-spacing: 0.06em;
  }

  .no-data {
    padding: 1.5rem;
    text-align: center;
    font-size: 0.8rem;
    color: var(--ink-faint);
    font-style: italic;
  }
</style>
"""


def _fmt_num(n: float, decimals: int = 3) -> str:
    if n == 0:
        return '<span class="num-zero">—</span>'
    return f"{n:,.{decimals}f}"


def _fmt_date(d) -> str:
    if pd.isna(d):
        return "—"
    try:
        return pd.Timestamp(d).strftime("%Y/%m/%d")
    except Exception:
        return str(d)


def build_html_report(
    data: dict,          # { code: {"name": str, "df": DataFrame, "qty": float} }
    date_start: str,
    date_end: str,
    title: str = "股利配息試算報表",
) -> str:
    now = datetime.now().strftime("%Y/%m/%d %H:%M")

    # ── 計算總計 ──
    total_est_cash  = 0.0
    total_est_stock = 0.0
    total_rows  = 0
    total_stocks = len(data)

    for info in data.values():
        df = info["df"]
        qty = info.get("qty", 0)
        if df.empty:
            continue
        total_est_cash  += (df["現金股利"] * qty * 1000).sum()
        total_est_stock += (df["股票股利"] * qty / 10).sum()
        total_rows  += len(df)

    # ── 摘要卡片 ──
    summary_html = f"""
    <div class="summary-row">
      <div class="summary-card">
        <div class="s-label">持股數</div>
        <div class="s-value">{total_stocks}<span class="s-unit">檔</span></div>
      </div>
      <div class="summary-card">
        <div class="s-label">配息次數</div>
        <div class="s-value">{total_rows}<span class="s-unit">次</span></div>
      </div>
      <div class="summary-card">
        <div class="s-label">預計現金收入</div>
        <div class="s-value">{total_est_cash:,.0f}<span class="s-unit">元</span></div>
      </div>
      <div class="summary-card">
        <div class="s-label">預計股票入帳</div>
        <div class="s-value">{total_est_stock:.3f}<span class="s-unit">張</span></div>
      </div>
    </div>
    """

    # ── 各股票區塊 ──
    blocks_html = ""
    for code, info in data.items():
        name = info["name"]
        df   = info["df"]
        qty  = info.get("qty", 0)
        error = info.get("error", "")

        sub_est_cash  = (df["現金股利"] * qty * 1000).sum() if not df.empty else 0
        sub_est_stock = (df["股票股利"] * qty / 10).sum() if not df.empty else 0
        count     = len(df)

        rows_html = ""
        if error:
            rows_html = f'<tr><td colspan="5" class="no-data">⚠ 查詢失敗：{error}</td></tr>'
        elif df.empty:
            rows_html = '<tr><td colspan="5" class="no-data">此區間無配息資料</td></tr>'
        else:
            for _, row in df.iterrows():
                badge = (
                    '<span class="badge badge-both">現金＋股票</span>'
                    if row["股票股利"] > 0
                    else '<span class="badge badge-cash">現金</span>'
                )
                
                rows_html += f"""
                <tr>
                  <td>{_fmt_date(row.get("_date") or row["除息日"])}</td>
                  <td>{_fmt_num(row["現金股利"])}</td>
                  <td>{qty}</td>
                  <td><strong>{_fmt_num(row["現金股利"] * qty * 1000, 0)}</strong></td>
                  <td>{badge}</td>
                </tr>"""

            # 小計行：顯示總額與總張數
            rows_html += f"""
            <tr class="subtotal-row">
              <td>{name} 小計</td>
              <td>—</td>
              <td>配股：{sub_est_stock:.3f} 張</td>
              <td>現金：${sub_est_cash:,.0f}</td>
              <td></td>
            </tr>"""

        blocks_html += f"""
        <div class="stock-block">
          <div class="stock-header">
            <span class="stock-badge">{code}</span>
            <span class="stock-name">{name}</span>
            <span class="stock-count">{count} 筆</span>
          </div>
          <table>
            <thead>
              <tr>
                <th style="width:20%">除息日</th>
                <th style="width:20%">現金股利（元）</th>
                <th style="width:20%">持有數量（張）</th>
                <th style="width:20%">預估現金入帳</th>
                <th style="width:20%">類型</th>
              </tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>"""

    # ── 合計列 ──
    total_html = f"""
    <div class="total-section">
      <div class="total-label">全部合計　{total_stocks} 檔</div>
      <div class="total-value">—</div>
      <div class="total-value">{total_est_stock:.3f}<span class="unit">張</span></div>
      <div class="total-value">{total_est_cash:,.0f}<span class="unit">元</span></div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{CSS}
</head>
<body>
<div class="report-wrap">

  <div class="report-head">
    <div class="report-meta">
      查詢區間：{date_start} ～ {date_end}<br>
      產生時間：{now}
    </div>
    <div class="report-title">{title}</div>
    <div class="report-subtitle">DIVIDEND INCOME REPORT</div>
  </div>

  {summary_html}
  {blocks_html}
  {total_html}

  <div class="report-foot">
    <span>資料來源：MoneyDJ 理財網</span>
    <span>產生時間 {now}</span>
  </div>

</div>
</body>
</html>"""

    return html