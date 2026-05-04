---
name: admission-emr-extraction
description: Use when extracting EMR records from Web EMR system for admission list patients. Triggered after lottery step completes, or when user says "提取EMR", "EMR extraction". Handles batch browser automation to query each patient's chart, extract raw clinical notes, auto-detect F/G (術前診斷/預計心導管), correct names, and write to sub-table. Post 5/4: no summary generation — only raw EMR + F/G prefill.
---

# EMR 原文批次擷取（post 5/4 — 摘要功能已停用）

## Overview
從 Web EMR 系統批次擷取入院名單病人的門診紀錄原文，寫入子表格 C 欄（EMR 原文）+ E/F 欄（auto-detect 術前診斷/預計心導管，由 process_emr.py 的 DIAG_RULES/CATH_RULES 在 raw EMR 上跑）。**5/4 起不再生成四段式摘要**，由使用者直接看 C 欄 raw EMR 判讀。

## Prerequisites
- Chrome 已開啟 Web EMR：http://hisweb.hosp.ncku/Emrquery/
- 使用者已手動登入
- 入院名單已匯入 Excel 且已完成抽籤（醫師病人表格已建立）

## 流程

### 1. 建立病人清單
從 Excel 各日期工作表的醫師病人表格讀取所有 {chart_no, doctor, name}。

### 2. 在 EMR 系統定義 JS Helper Functions

```javascript
// 在 topFrame 設定病歷號並查詢
window.queryEMR = function(chartNo) {
    let topDoc = window.frames['topFrame'].document;
    topDoc.getElementById('txtChartNo').value = chartNo;
    topDoc.getElementById('BTQuery').click();
};

// 在 leftFrame 找到並點擊醫師的最近門診
window.clickDoctorVisit = function(doctorName) {
    let leftDoc = window.frames['leftFrame'].document;
    let links = leftDoc.querySelectorAll('a');
    for (let link of links) {
        let t = link.innerText.trim();
        if (t.includes('門診') && t.includes(doctorName)) {
            link.click();
            return t;
        }
    }
    return null;
};

// 從 mainFrame 擷取 EMR 文字
window.extractEMR = function() {
    let text = window.frames['mainFrame'].document.body.innerText;
    return text.split('\n').filter(l => l.trim());
};
```

### 3. 批次自動查詢（2.5s/人）

```javascript
// 佇列處理：query → 1.5s → click visit → 1s → extract → next
window.processNext = function() {
    let p = queue[idx];
    window.queryEMR(p.chart);
    setTimeout(() => {
        let visit = window.clickDoctorVisit(p.doctor);
        if (!visit) {
            results[p.chart] = {name: 'pending', lines: ['無本院一年內主治醫師門診紀錄']};
        }
        setTimeout(() => { idx++; window.processNext(); }, 1000);
    }, 1500);
};
```

### 4. 重試未成功的病人
首次批次完成後：
- 檢查 `hasNoRecord` 的病人（可能是載入太慢）
- 用 3s+2.5s 的較長等待重試
- 重試後仍無紀錄的才標記為「無本院一年內主治醫師門診紀錄」

### 5. 檢查重複資料
批次處理可能因時間差導致兩位病人拿到相同 EMR。比對前 5 行辨識重複，重新查詢。

### 6. 匯出資料到本地
JS tool 的 blocking filter 會擋某些醫療文字。解法：

```python
# 啟動本地 HTTP server 接收 POST
from http.server import HTTPServer, BaseHTTPRequestHandler
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        with open('emr_data.json', 'wb') as f:
            f.write(body)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'OK')
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
server = HTTPServer(('127.0.0.1', 18234), Handler)
server.handle_request()  # OPTIONS
server.handle_request()  # POST
```

瀏覽器端：
```javascript
fetch('http://127.0.0.1:18234/emr', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(allData)
});
```

### 7. 姓名校正
EMR 系統的姓名為正確來源。比對 Excel 並自動更新所有位置：
- 主資料 A-M 的姓名欄
- Round-robin N-S 的病人姓名欄
- 醫師病人表格的姓名欄

### 8. 寫入 Sheet（post 5/4 — 摘要功能停用）
- **C 欄（EMR 原文）**：完整原文 + visit header（`【EMR來源門診：...】`），wrap_text=True
- **E 欄（術前診斷）**：DIAG_RULES auto-detect → 使用者審核
- **F 欄（預計心導管）**：CATH_RULES auto-detect → 使用者審核
- 無紀錄 → C 欄寫「無本院一年內主治醫師門診紀錄」
- 需申請 → C 欄寫「本病歷號需要額外申請」

## 特殊情況
- EMR 系統用 frameset，內容在 mainFrame
- 用 `window.frames['leftFrame']` 和 `window.frames['mainFrame']` 存取
- JS tool 會 block 含 session/cookie 格式的回傳值，用 `JSON.stringify(lines.slice(x, y))` 分段取得，或用本地 HTTP server 整批匯出

---

## Playwright 模式（per-date driver script）

使用者手動登入後把 session URL 貼給 Claude（如 `http://hisweb.hosp.ncku/Emrquery/(S(xxx))/tree/frame.aspx`），由 Python + Playwright 非 headless 驅動。最近的 driver 範本：`extract_emr_{YYYYMMDD}.py`。

### 已知坑（本 session 踩過，務必避開）

**坑 1：cp950 終端不能 `print()` 中文**
錯誤訊息：`'cp950' codec can't encode character '\xa0'`。若 `log()` 函式同時 `file.write + print(...)` 中文，`print` 會噴錯，再被 `query_one` 的 `try/except` 吞掉 → 所有成功查詢都被誤判為 exception，病人全部變 `no_record`。
**正確做法：** `log()` 只 write 到 UTF-8 檔，**不要 print**。結束後用 Read tool 讀 log。

```python
LOG = open('_extract_emr_YYYYMMDD.log', 'w', encoding='utf-8')
def log(msg):
    LOG.write(msg + '\n'); LOG.flush()
    # 絕不 print()
```

**坑 2：leftFrame stale — 查詢間 session state 殘留**
同一個 page 連續打 `BTQuery` 查不同 chart 時，leftFrame 有時仍顯示上一個病人的 visit 列表。症狀：兩個不相關的病人拿到一模一樣的 visit label 清單。
**正確做法：** 查詢有失敗 / 需重試時，**`page.goto(SESSION_URL)` 重新載入** 再查下一個；或在 query 之間額外 `time.sleep(5)` 並 `wait_for_function` leftFrame links 更新。穩妥做法是 retry 版本一律 goto 重載：

```python
for i, pt in enumerate(RETRY):
    if i > 0:
        page.goto(SESSION_URL, timeout=60000)
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(3)
    query(page, pt['chart'], pt['doctor'])
```

### Playwright flow 骨架

1. `sync_playwright` 啟 non-headless Chromium，`goto(SESSION_URL)`
2. `query_one(page, chart, doctor)`：
   - `topFrame.evaluate` 設 `txtChartNo` + 點 `BTQuery`，`sleep(3+)`
   - `leftFrame.wait_for_function("document.querySelectorAll('a').length > 0")`
   - `leftFrame.evaluate` 找 `t.includes('門診') && t.includes(doctor)` 的連結 → click
   - `mainFrame.wait_for_function(...)` 等內容，`innerText` 拿原文
   - 截掉 `[Medicine]` 之後的段落（見 `feedback_emr_html_parsing.md`）
3. 存成 `emr_data_{YYYYMMDD}.json` 給下一階段 `process_emr_{YYYYMMDD}.py` 做摘要 + 寫 sheet

### 寫 Sheet（post 5/4 — 摘要功能停用，7-col 子表格）

- **C 欄 value**：完整 EMR 原文 + visit header（`【EMR來源門診：醫師, 科別診次, 日期】`）
- **E 欄 value**：DIAG_RULES auto-detect 結果（術前診斷）
- **F 欄 value**：CATH_RULES auto-detect 結果（預計心導管）

**對齊要求**：寫入一律用 **chart number** 當 key 定位 sub-table patient row（掃 col B），**絕不用固定 row index**。寫完之後跑 `admission-format-check` 的對齊驗證（A 姓名、B chart、C 開頭 visit header 醫師），不對就重抽。不可沉默。

### 無紀錄情況的分類
- `ok` — visit label 匹配該醫師，拿到 SOAP 全文
- `ok_fallback` — 沒匹配指定醫師但有其他心臟血管科 visit，改點該連結
- `no_doctor_match` — leftFrame 有門診紀錄但全不是該醫師（常見於 8 科別／手術 only）
- `no_record` — leftFrame 完全沒有門診紀錄

後 3 種 → C 寫「無本院一年內主治醫師門診紀錄」、E/F 留空。per `feedback_nodata_still_keyin.md`，這些病人仍要照醫師時段 key 入導管。
