"""
app.py
股利配息追蹤器 — 預設持股完整版
執行：streamlit run app.py
"""
import io
import re
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from scraper import fetch_dividends, get_stock_name
from report  import build_html_report
from exporter import export_png, export_pdf

# ── 頁面設定 ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="股利配息追蹤器",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 自訂 CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
  :root { --sage-dark: #4a6b4d; --gold: #b8a87a; --ink: #2c2c2a; }
  #MainMenu, footer, header { visibility: hidden; }
  [data-testid="stSidebar"] { background: #f5f3f0; border-right: 1px solid #ddd9d3; }
  .stButton > button { background: #4a6b4d; color: white; border-radius: 6px; padding: 0.5rem; }
  .stDownloadButton > button { background: #b8a87a; color: white; border-radius: 6px; }
  .stock-tag { display: inline-block; background: #c8dac9; color: #4a6b4d; border-radius: 4px; padding: 3px 10px; font-size: 0.82rem; margin: 2px 3px; font-family: monospace; }
  h2 { color: #2c2c2a !important; font-weight: 400 !important; }
  h3 { color: #5f5e5a !important; font-weight: 400 !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar：查詢與持股設定 ───────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 股利配息追蹤器")
    st.markdown("---")

    st.markdown("### 1. 設定持股 (1張=1000股)")
    
    # 設定預設持股資料
    default_stocks = [
        {"code": "0050", "qty": 18.0},
        {"code": "0056", "qty": 11.0},
        {"code": "00919", "qty": 12.0},
        {"code": "00687B", "qty": 9.0},
        {"code": "00795B", "qty": 10.0}
    ]

    if "stock_input_list" not in st.session_state:
        st.session_state.stock_input_list = default_stocks

    # 動態產生輸入框
    updated_list = []
    for i, item in enumerate(st.session_state.stock_input_list):
        c1, c2 = st.columns([2, 1.2])
        with c1:
            u_code = st.text_input(f"代碼_{i}", value=item["code"], key=f"code_in_{i}", label_visibility="collapsed").upper()
        with c2:
            u_qty = st.number_input(f"張數_{i}", value=item["qty"], min_value=0.0, step=0.1, key=f"qty_in_{i}", label_visibility="collapsed")
        updated_list.append({"code": u_code, "qty": u_qty})
    
    st.session_state.stock_input_list = updated_list

    col_add, col_clr = st.columns(2)
    if col_add.button("➕ 新增股票", use_container_width=True):
        st.session_state.stock_input_list.append({"code": "", "qty": 1.0})
        st.rerun()
    if col_clr.button("🗑️ 全部清空", use_container_width=True):
        st.session_state.stock_input_list = [{"code": "", "qty": 1.0}]
        st.rerun()

    st.markdown("---")
    st.markdown("### 2. 查詢區間")
    date_start = st.date_input("開始日期", value=date.today() - timedelta(days=365))
    date_end = st.date_input("結束日期", value=date.today())

    st.markdown("---")
    query_btn = st.button("🔍 開始計算配息", use_container_width=True)

    st.markdown("---")
    st.markdown("### 3. 匯出設定")
    pdf_password = st.text_input("PDF 密碼 (選填)", type="password", placeholder="留空則不加密")

# ── 主畫面邏輯 ────────────────────────────────────────────────────────
st.markdown("# 股利配息試算報表")
st.markdown("自動計算指定期間內，持有張數所對應的預計現金收益。")
st.markdown("---")

if "report_data" not in st.session_state:
    st.session_state.report_data = None
if "report_html" not in st.session_state:
    st.session_state.report_html = None

# ── 執行查詢與計算 ────────────────────────────────────────────────────
if query_btn:
    input_map = {item["code"]: item["qty"] for item in st.session_state.stock_input_list if item["code"]}
    codes = list(input_map.keys())

    if not codes:
        st.warning("請至少輸入一個股票代碼")
    elif date_start > date_end:
        st.error("開始日期不能晚於結束日期")
    else:
        progress_bar = st.progress(0, text="連線至 MoneyDJ...")
        
        names = {c: get_stock_name(c) for c in codes}
        
        def on_progress(i, total, code):
            progress_bar.progress(int((i / total) * 100), text=f"正在分析 {code} ({i+1}/{total})...")

        raw_data = fetch_dividends(codes, str(date_start), str(date_end), progress_callback=on_progress)
        progress_bar.progress(100, text="計算完成！")

        report_data = {}
        for code in codes:
            df = raw_data.get(code, pd.DataFrame())
            qty = input_map.get(code, 0)
            
            if not df.empty:
                # 核心試算邏輯：金額 * 張數 * 1000
                df["持有張數"] = qty
                df["預估現金股利"] = df["現金股利"] * qty * 1000
                df["預估總股利"] = df["合計股利"] * qty * 1000
            
            report_data[code] = {
                "name": names.get(code, code),
                "df": df,
                "qty": qty,
                "error": df.attrs.get("error", ""),
            }

        st.session_state.report_data = report_data
        st.session_state.date_start = str(date_start)
        st.session_state.date_end = str(date_end)
        st.session_state.report_html = build_html_report(report_data, str(date_start), str(date_end))
        st.rerun()

# ── 顯示結果與匯出 ────────────────────────────────────────────────────
if st.session_state.report_html:
    res = st.session_state.report_data
    html_content = st.session_state.report_html
    
    # 摘要計算
    total_cash = sum(info["df"]["預估現金股利"].sum() for info in res.values() if not info["df"].empty)
    total_all = sum(info["df"]["預估總股利"].sum() for info in res.values() if not info["df"].empty)
    total_count = sum(len(info["df"]) for info in res.values())
    
    m1, m2, m3 = st.columns(3)
    m1.metric("標的總數", f"{len(res)} 檔")
    m2.metric("預估現金入帳合計", f"${total_cash:,.0f} 元")
    m3.metric("配息總次數", f"{total_count} 次")

    st.markdown("---")
    st.components.v1.html(html_content, height=600, scrolling=True)

    # ── 匯出按鈕區 ──
    st.markdown("### 📥 匯出報表")
    col_png, col_pdf, col_csv = st.columns(3)

    with col_png:
        if st.button("🖼️ 匯出 PNG 圖片", use_container_width=True):
            with st.spinner("渲染中..."):
                try:
                    png_bytes = export_png(html_content)
                    st.download_button("⬇ 下載 PNG", data=png_bytes, file_name="股利報表.png", mime="image/png", use_container_width=True)
                except Exception as e:
                    st.error(f"PNG 匯出失敗: {e}")

    with col_pdf:
        if st.button("📄 匯出 PDF", use_container_width=True):
            with st.spinner("產生 PDF..."):
                try:
                    pdf_bytes = export_pdf(html_content, password=pdf_password)
                    st.download_button("⬇ 下載 PDF", data=pdf_bytes, file_name="股利報表.pdf", mime="application/pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"PDF 匯出失敗: {e}")

    with col_csv:
        all_dfs = []
        for code, info in res.items():
            if not info["df"].empty:
                temp_df = info["df"].copy()
                temp_df.insert(0, "名稱", info["name"])
                temp_df.insert(0, "代碼", code)
                all_dfs.append(temp_df)
        
        if all_dfs:
            csv_df = pd.concat(all_dfs, ignore_index=True)
            # 移除隱藏欄位
            csv_df = csv_df[[c for c in csv_df.columns if not c.startswith("_")]]
            csv_data = csv_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("⬇ 下載 CSV 明細", data=csv_data, file_name="股利明細.csv", mime="text/csv", use_container_width=True)

else:
    st.markdown("""
    <div style="text-align:center; padding:5rem 2rem; color:#9a9790;">
      <div style="font-size:3rem; opacity:0.3;">📊</div>
      <p>左側已預設您的持股，請確認區間後點擊「開始計算配息」。</p>
    </div>
    """, unsafe_allow_html=True)