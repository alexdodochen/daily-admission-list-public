---
name: EMR fallback 只限六位醫師
description: 當目標主治醫師無一年內門診時，EMR fetch 只允許 fallback 到特定六位醫師，否則標記無資料病人
type: feedback
---

目標主治醫師沒有一年內門診時，`fetch_emr.py` 只能 fallback 點擊以下六位醫師的門診紀錄：
- 劉秉彥
- 趙庭興
- 蔡惟全
- 許志新
- 陳柏升
- 李貽恒

都找不到就回傳 no_visit → `process_emr` 會寫「無本院一年內主治醫師門診紀錄」→ 走無資料病人流程。

**Why:** 這六位醫師的 SOAP note 內容品質可信、有完整心臟科背景，其他科別（例如眼科、骨科）的門診就算同一個病人也沒有心臟相關資訊，抓回來會誤導摘要與 F/G 預填。

**安全性推論（2026-04-16 實驗驗證）：** EMR 查詢是 chart-based（`txtChartNo` 查詢），`#divUserSpec` 永遠跟著查詢的病歷號回填該病人的姓名/生日/性別 —— 不管點了哪一筆 visit。所以姓名/年齡/性別自動校正「只要病歷號對就寫回」是安全的，fallback 只會污染 SOAP 內容，不會污染 header 基本資料。實測 3 筆 fallback 案例（4/20 戴宗訓/沈維護→劉秉彥、4/21 陳爽→李昱逵眼科）的 `#divUserSpec` 都正確對應。

**How to apply:** 修改 `fetch_emr.py` 的 `_click_visit` 時，fallback 迴圈必須限定這六位白名單。EMR 姓名/年齡/性別仍要從 `#divUserSpec` 抓取並校正 Google Sheet —— 姓名更新到主資料 F 欄+子表格 A 欄，年齡由生日推算寫 H 欄，性別寫 G 欄，不受 visit 是否成功影響，只要病歷號正確。
