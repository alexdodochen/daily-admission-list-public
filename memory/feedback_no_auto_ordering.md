---
name: N-V ordering 不自動跑
description: N-V 入院序 round-robin 任何情境下都不自動跑，使用者明確指示「跑入院序 / 排序 / 抽籤」才動
type: feedback
---

規則：N-V 入院序（round-robin / 排住院序）**永遠不自動跑**。即便是新建日期 sheet、diff-update 加新病人、cancel 病人重編，也都不要自動執行 lottery / round-robin。等使用者明確指示「跑入院序」「排序」「抽籤」「重排」才能動。

**Why:** 使用者多次提醒：N-V 是手動敲定欄位（依床位、家屬、臨床狀況調整），Claude 自動跑 round-robin 會把這些調整沖掉，且使用者要把握主動權決定何時定案。原有 `feedback_preserve_manual_ordering.md` 是「不可覆寫已有的 N-V」；此規則是更廣的「永不自動跑」——即便 N-V 為空、即便是新增病人，也都等使用者點頭。

**How to apply:**
- 收到「匯入入院名單 / diff-update / 加新病人」指令 → 只動主資料 + 子表格 + EMR，**N-V 留空**或保留現狀
- 不要主動建議「要不要重跑入院序」之類；使用者要排會自己說
- 收到「跑入院序」「排序」「抽籤」「重排」「lottery」「round-robin」「定案」明確字樣才執行 admission-lottery / admission-ordering 流程
- 若 N-V 已部分填寫但有空缺，**也別自動補**——使用者可能就是要保持那樣
