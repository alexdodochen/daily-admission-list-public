---
name: EMR HTML 擷取範圍規則
description: EMR 頁面只擷取包含 SOAP note 的 div.small，其餘區塊一律略過
type: feedback
---

EMR 擷取時，**只讀取**包含 [Diagnosis][Subjective][Objective][Assessment & Plan] 的 `<div class="small">` 區塊。

以下區塊**一律略過，不擷取**：
- `<div class="iportlet-content">` — 檢查報告（EKG、心臟超音波等文字報告）
- `<div class="plan">` — 開立醫囑、檢驗單、住院許可等
- `<div class="medicine">` — 藥物清單

**Why:** 這些區塊不是臨床評估內容，混入摘要會造成資料冗長且干擾判讀。

**How to apply:** 解析 EMR HTML 時，先定位含有 [Diagnosis] 或 [Subjective] 關鍵字的 `<div class="small">`，只處理該區塊的文字；其餘 div 標籤不納入。
