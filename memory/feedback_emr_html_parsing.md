---
name: EMR HTML 擷取範圍規則
description: EMR 頁面只擷取包含 SOAP note 的 div.small，其餘區塊一律略過
type: feedback
---

EMR 擷取時，**只讀取** [Diagnosis][Subjective][Objective][Assessment & Plan] 四個區塊。

**截止點：遇到 `[Medicine]` 或 `[Plan : 依類別]` 立刻停止，後面的內容一律不擷取。**

以下內容**一律略過，不擷取**：
- `[Medicine]` — 藥物清單（CoPlavix, Cretrol 等）
- `[Plan : 依類別]` — 藥品、檢驗、掛號、醫病共享決策等
- `-----藥品-----` / `-----檢驗-----` / `-----其他-----` 分隔線後的所有內容
- `<div class="iportlet-content">` — 檢查報告
- `<div class="plan">` — 醫囑
- `<div class="medicine">` — 藥物
- `執行時間 :` 開頭的行

**Why:** 藥品清單、檢驗單、掛號作業不是臨床評估內容，混入摘要會造成資料冗長且干擾判讀。使用者多次反映 [Medicine] 和 [Plan] 區塊不應出現在 EMR 摘要中。

**How to apply:** 解析 EMR 文字時，從 [Diagnosis] 開始擷取，到 [Assessment & Plan] 的實質內容結束。一遇到 [Medicine]、[Plan : 依類別]、`-----藥品-----` 或 `執行時間` 就截止。
