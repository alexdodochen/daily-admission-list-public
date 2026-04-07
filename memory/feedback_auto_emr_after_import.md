---
name: 匯入病人後自動開始EMR摘要
description: 病人資料匯入確認後，自動開始整理主治醫師病人清單和EMR摘要，不需額外指令
type: feedback
---

病人資料匯入並確認病歷號碼正確後，自動進入下一步：整理主治醫師病人清單 + EMR 摘要擷取。

**Why:** 減少手動下指令的步驟，匯入→確認→EMR 是固定流程，不需要每次都問。
**How to apply:**
- 使用者確認病歷號碼正確後，立即請使用者提供 EMR session URL
- 拿到 session URL 後自動批次查詢所有病人的 EMR
- EMR 摘要完成後自動寫入 Sheet 的醫師病人表格 C/D 欄
