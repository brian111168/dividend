"""
scraper.py
爬取 MoneyDJ 配息資料 + TWSE 股票名稱查詢
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import certifi

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.moneydj.com/",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ── 股票名稱查詢 ─────────────────────────────────────────────────────
def get_stock_name(code: str) -> str:
    """
    查詢股票/ETF 中文名稱。
    先查 TWSE，再查 MOPS，找不到就回傳代碼本身。
    """
    code = code.strip().upper()

    # 嘗試 TWSE 上市
    try:
        url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
        resp = requests.get(url, timeout=8)
        if resp.ok:
            data = resp.json()
            for item in data:
                if item.get("Code", "").strip() == code:
                    return item.get("Name", code).strip()
    except Exception:
        pass

    # 嘗試 MOPS 上櫃
    try:
        url = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"
        resp = requests.get(url, timeout=8)
        if resp.ok:
            data = resp.json()
            for item in data:
                if item.get("SecuritiesCompanyCode", "").strip() == code:
                    return item.get("CompanyName", code).strip()
    except Exception:
        pass

    return code  # 查不到就回傳代碼


# ── MoneyDJ 配息資料 ─────────────────────────────────────────────────
def _moneydj_url(code: str) -> str:
    """
    組出 MoneyDJ 配息頁 URL。
    台股代碼加 .TW，已有 .TW 則直接用。
    """
    code = code.strip().upper()
    if not code.endswith(".TW"):
        code = code + ".TW"
    return f"https://www.moneydj.com/ETF/X/Basic/Basic0005.xdjhtm?etfid={code}"


def scrape_moneydj(code: str) -> pd.DataFrame:
    """
    爬取 MoneyDJ 單一股票/ETF 的配息歷史表格（通用穩定版）
    回傳 DataFrame：columns = [除息日, 現金股利, 股票股利, 合計股利]
    """
    url = _moneydj_url(code)

    try:
        resp = SESSION.get(url,  verify=False, timeout=15)
        resp.encoding = "utf-8"
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"無法連線到 MoneyDJ（{code}）：{e}")

    soup = BeautifulSoup(resp.text, "lxml")

    # 找目標 table（含配息關鍵字）
    target = None
    for t in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in t.find_all("th")]
        text = " ".join(headers)
        if any(k in text for k in ["除息", "配息", "股利"]):
            target = t
            break

    if target is None:
        return pd.DataFrame(columns=["除息日", "現金股利", "股票股利", "合計股利"])

    # ===== 工具函式 =====
    def parse_num(s):
        s = s.replace(",", "").strip()
        try:
            return float(s)
        except:
            return 0.0

    def parse_date(s):
        s = s.strip()
        for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(s, fmt).strftime("%Y/%m/%d")
            except:
                pass

        # 民國年
        m = re.match(r"(\d{2,3})/(\d{1,2})/(\d{1,2})", s)
        if m:
            y = int(m.group(1))
            if y < 1911:
                y += 1911
            return f"{y}/{int(m.group(2)):02d}/{int(m.group(3)):02d}"
        return ""

    def find_idx(headers, keywords):
        for i, h in enumerate(headers):
            if any(k in h for k in keywords):
                return i
        return None

    # ===== 解析 header =====
    headers = [th.get_text(strip=True) for th in target.find_all("th")]

    idx_date = find_idx(headers, ["除息"])
    idx_cash = find_idx(headers, ["現金股利", "配息總額"])
    idx_stock = find_idx(headers, ["股票股利"])

    rows = []

    for tr in target.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if not cols:
            continue

        # 日期
        date = parse_date(cols[idx_date]) if idx_date is not None and idx_date < len(cols) else ""

        # 現金（ETF通常在「配息總額」）
        cash = parse_num(cols[idx_cash]) if idx_cash is not None and idx_cash < len(cols) else 0.0

        # 股票股利（有些沒有）
        stock = parse_num(cols[idx_stock]) if idx_stock is not None and idx_stock < len(cols) else 0.0

        total = cash + stock

        if not date:
            continue

        rows.append({
            "除息日": date,
            "現金股利": cash,
            "股票股利": stock,
            "合計股利": total,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["_date"] = pd.to_datetime(df["除息日"], errors="coerce")
    df = df.sort_values("_date", ascending=False).reset_index(drop=True)

    return df


def fetch_dividends(
    codes: list[str],
    date_start: str,
    date_end: str,
    progress_callback=None,
) -> dict[str, pd.DataFrame]:
    """
    批次查詢多檔股票配息。
    date_start / date_end：字串格式 YYYY-MM-DD
    回傳 dict：{ code: DataFrame }
    """
    start = pd.Timestamp(date_start)
    end   = pd.Timestamp(date_end)
    result = {}

    for i, code in enumerate(codes):
        if progress_callback:
            progress_callback(i, len(codes), code)

        try:
            df = scrape_moneydj(code)
            if not df.empty and "_date" in df.columns:
                df = df[
                    (df["_date"] >= start) & (df["_date"] <= end)
                ].copy()
            result[code] = df
        except Exception as e:
            # 查詢失敗：回傳空 DataFrame 並附上錯誤訊息
            empty = pd.DataFrame(columns=["除息日", "現金股利", "股票股利", "合計股利"])
            empty.attrs["error"] = str(e)
            result[code] = empty

        # 禮貌性延遲，避免被 ban
        if i < len(codes) - 1:
            time.sleep(0.8)

    return result
