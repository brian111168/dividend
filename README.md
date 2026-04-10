# 股利配息追蹤器

台股 / ETF 配息查詢工具，資料來源為 MoneyDJ 理財網，無需付費 API。

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 安裝 Playwright（PNG / PDF 匯出用）

```bash
playwright install chromium
```

> 若不需要 PNG/PDF 匯出，可跳過此步驟，CSV 匯出不需要。

### 3. 啟動

```bash
streamlit run app.py
```

瀏覽器會自動開啟 `http://localhost:8501`

---

## 功能

- 輸入多個股票代碼（台股、ETF 均可）
- 自訂查詢日期範圍
- 自動查詢 MoneyDJ 配息歷史
- 美化 HTML 報表（低彩度、高級配色）
- 匯出：PNG 圖片 / PDF（可加密）/ CSV

## 檔案結構

```
dividend_tracker/
├── app.py          # Streamlit 主介面
├── scraper.py      # MoneyDJ 爬蟲 + 股票名稱查詢
├── report.py       # HTML 報表產生器
├── exporter.py     # PNG / PDF 匯出
├── requirements.txt
└── README.md
```

## 匯出說明

| 格式 | 需要套件 | 說明 |
|------|---------|------|
| CSV  | 無額外需求 | 永遠可用 |
| PNG  | playwright + chromium | 高畫質截圖 |
| PDF  | playwright 或 weasyprint | 可加密（AES-256） |

## 注意事項

- 資料來源為 MoneyDJ，爬取時有 0.8 秒延遲以避免被封鎖
- 股票名稱查詢使用 TWSE / TPEX 公開 API
- 僅供個人參考，不構成投資建議
"# dividend" 
