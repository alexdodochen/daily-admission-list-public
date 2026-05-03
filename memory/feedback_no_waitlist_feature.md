---
name: 續等清單功能已永久移除
description: 2026-04-19 起續等清單（waitlist）全面下線——無 sheet、無欄、無 LINE cron、無定案整合，非時段醫師直接接 round-robin
type: feedback
---

2026-04-19 使用者要求**永久移除**每日續等清單功能。所有相關元件已清除：

- **Google Sheet**：「每天續等清單」worksheet 已刪除
- **欄位**：YYYYMMDD sheet 的 ordering 從 N-W (10 欄) 改為 N-V (9 欄)。原 V=每日續等清單刪除，原 W=改期 移到 V
- **Skills**：`admission-lottery` 的「每日續等抽籤」「整合入院清單（產生定案）」兩節已移除；`admission-ordering` 不再把非抽籤表醫師移到續等
- **LINE Bot**（私有基礎建設，public mirror 不應出現細節）：對應 cron job 已刪除；對應 endpoint 待從 bot 移除
- **Memory**：`feedback_waitlist_merge.md`、`feedback_webapp_no_waitlist_integration.md` 已刪

**Why:** 使用者明確表示「不需要每日續等清單這個功能了 幫我清除掉」，並授權刪 worksheet + 清全部相關。續等流程原本是「未入院病人歸檔 + 下次抽籤優先」，已不再需要此工作流。

**How to apply:**
- 不再需要處理「續等清單」、「每天續等清單」、「定案整合」任何相關指令
- 非抽籤表（非時段）醫師病人：**直接接在主 round-robin 最後**，不另開 sheet、不另外抽籤
- 如果使用者之後又要求類似功能，當作**新功能**重新規劃（而非找回舊實作）
- 若在舊 commit/memory/doc 看到續等清單相關敘述，視為歷史存檔，不得重新啟用
