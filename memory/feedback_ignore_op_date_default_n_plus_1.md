---
name: feedback_ignore_op_date_default_n_plus_1
description: 入院清單截圖的「開刀日」(col B) 不可信，全部以「sheet 對應日 = 入院日」為準，cathlab 預設 N+1，使用者明說才改
type: feedback
originSessionId: a237e859-cb18-4efd-8aa5-0e8ae104bf8e
---
每日入院清單截圖中：
- **col A 實際住院日 = sheet 對應日**（例 5/3 入院清單 → 全部 8 人 admit 5/3）
- **col B 開刀日 一律忽略**（截圖中可能顯示 5/4 / 5/5 等不同日期，全部不可信）
- **cathlab 預設 = 入院日 +1（N+1）**，週五入院 → 同日（rule #5 例外）
- **使用者明說「某病人改 X/Y 做 cathlab」才改 V 欄**（rule #5 reschedule）

**Why:** 2026-04-26 處理 5/3 截圖時我把 col A 的 5/3/5/4/5/5 當成不同 admit 日期，自作聰明拆三個 sheet 並嘗試針對不同 cathlab 日 lottery。使用者糾正：「忽略開刀日!! 這些人就都是 5/3 住院，除非我特別跟你說，就都是隔日做導管，所以他們都要放 5/3 入院工作表!!」

**How to apply:**
- 收到 {MMDD} 入院截圖 → 全部 patients 寫進 `2026MMDD` sheet，col A 統一寫 `2026-MM-DD`，col B 統一寫 N+1（如 `2026-05-04`）
- 不要因為截圖 col A/B 看到不同日期就拆 sheet 或質疑入院日
- Lottery / cathlab 全部走單一日（admit day +1），不要分多日 round-robin
- V 欄改期是純人工標記，無人工指示就不動
