---
description: 心導管排程 key-in，用 Playwright 自動化 WEBCVIS 系統新增病人排程。觸發：使用者說「導管排程」「key-in導管」「排導管」。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
---

## 步驟六：心導管排程 key-in

### 系統資訊
- URL: `http://cardiopacs01.hosp.ncku:8080/WEBCVIS/HCO/HCO1W001.do`
- 帳號/密碼: 107614 / 107614
- 入院日 N → 導管排在 N+1

### 流程

1. 讀取入院序列表格（N-U 欄），取得每位病人的術前診斷、預計心導管
2. 查「主治醫師導管時段表」確定檢查室和時間
3. 生成 `cathlab_keyin_MMDD.py` 腳本（參考 `cathlab_keyin_0410.py` 範本）
4. 用 Playwright 執行：Phase 1 ADD 新增 → Phase 2 UPT 補 pdijson/phcjson
5. 最終驗證所有病人是否成功寫入

### 時間規則
- **上午**: 0600 起，每人 +1（0600, 0601, 0602...）
- **下午**: 1730 起，每人 +1（1730, 1731, 1732...）
- **非時段**: H1 1800 起，每人 +1

### 檢查室代碼
H1→xa-Hybrid1, H2→xa-Hybrid2, C1→xa-CATH1, C2→xa-CATH2

### 第二主刀醫師（括號簡稱）
寬→葉建寬(105234), 浩→葉立浩(105430), 晨→洪晨惠(636042), 齡→許毓軨(101696), 嘉→蘇奕嘉(102180)

### WEBCVIS 技術細節
- 日期欄位 `daySelect1`/`daySelect2` 為 readonly → 需 `removeAttribute('readonly')` 後設值
- `QueryButton` 是 `<button>` → 用 `document.getElementById("QueryButton").click()`
- `buttonName` input 的 `.name` 設為 "ADD"/"SAVE"/"QRY"/"UPT" 後 submit
- `pdijson`/`phcjson` 是 hidden input，JSON 格式 `[{"name":"...","id":"PDI..."}]`
- `SaveButton` 必須用 `page.click('#SaveButton')` 觸發 jQuery handler

### 安全規則
- **絕對不更動現有排程** — 只新增，不修改、不刪除
- 已存在的病人（比對病歷號）不重複新增
- **李柏增不填入主刀/第二主刀醫師欄位**
- 備註含「不排程」→ 直接跳過
- 備註含「檢查」（如入院檢查貧血）→ 直接跳過（非導管床/HF AE 不一定跳過，只有「檢查」才跳過）
- 無資料病人 → 照主治醫師時段排入，備註填「無資料病人」
- 預計心導管不在 WEBCVIS 選單時 → 改填 note 欄位
- 第二醫師多人時（如「浩、晨」）→ attendingdoctor2 填葉立浩，其餘放備註（如 note="晨"）
