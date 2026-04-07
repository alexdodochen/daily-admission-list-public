---
description: 自動擷取 EMR 病歷摘要並寫入 Sheet。觸發：病人匯入確認後自動開始、使用者說「EMR」「摘要」「提取EMR」、使用者貼 EMR session URL。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
---

## 步驟三：EMR 病歷摘要擷取

### 前提
- 使用者手動在 Chrome 開啟 Web EMR (`http://hisweb.hosp.ncku/Emrquery/`) 並登入（有 CAPTCHA，不可自動登入）
- 使用者貼 session URL（格式：`(S(xxxxx))/tree/frame.aspx`）

### 流程

1. **請使用者提供 EMR session URL**

2. **用 Playwright 帶 session URL 批次查詢所有病人**：
   - 搜尋框 ID: `txtChartNo`
   - EMR frame 結構：`top.aspx`(病人資料) → `list3.aspx`(就醫紀錄樹) → content frame(SOAP note)
   - **搜尋策略**（依優先順序）：
     1. 心臟血管科門診紀錄
     2. 同一位主治醫師的門診紀錄（不限科別）
     3. 任何門診紀錄
   - 從 `top.aspx` 取得正確姓名，與 Sheet 比對並更新錯誤名字

3. **生成四段式摘要**：
   ```
   一、心臟科相關診斷
   二、病史
   三、客觀檢查
   四、本次住院計畫
   ```

4. **自動寫入 Sheet**（不需再問使用者確認）：
   - C 欄 = 完整 EMR 原文
   - D 欄 = 四段式摘要
   - 無紀錄 → C 欄寫「無本院一年內主治醫師門診紀錄」

5. **無資料病人處理**（EMR 查無紀錄時自動執行）：
   - H 欄（註記）寫「無資料病人」
   - 複製一份到「無資料病人」工作表（格式：預計入院日期 | 主治醫師 | 姓名 | 病歷號 | 備註）
   - 寫入前檢查病歷號是否已存在，避免重複

### 重要規則
- **絕對不要自己開瀏覽器登入 EMR**，等使用者手動登入後貼 session URL
- EMR 摘要完成後**自動寫入 Sheet**，不需再問確認
- 用 EMR 上的正確姓名回頭更新 Sheet 上的錯誤名字
- 寫入前先檢查目標區域為空，不覆蓋現有資料
