---
name: EMR 系統由使用者手動開啟登入
description: EMR擷取前不要自己開瀏覽器或嘗試登入，等使用者手動開啟並登入後再去抓資料
type: feedback
---

EMR 系統 (hisweb.hosp.ncku/Emrquery/) 一律由使用者手動在 Chrome 開啟並登入，Claude 不要自己嘗試開啟或登入。

**Why:** EMR 登入頁有 CAPTCHA 驗證碼，Playwright 無法自動通過。
**How to apply:**
- 使用者手動登入後，貼 session URL（格式：`(S(xxxxx))/tree/frame.aspx`）
- Claude 用 Playwright 帶該 session URL 開啟，直接查詢病人
- 或使用者直接貼 EMR 截圖，Claude 從圖片做摘要
- EMR frame 結構：`top.aspx`(病人資料) → `list3.aspx`(就醫紀錄樹) → content frame(SOAP note)
- 搜尋輸入框 ID: `txtChartNo`
- EMR 摘要完成後自動寫入 Sheet，不需再問使用者確認
- **搜尋門診紀錄時對主治醫師名字**，不是對科別
- **找不到主治醫師門診時**，依序找以下備選醫師的門診紀錄：劉秉彥、趙庭興、蔡惟全、陳柏升、許志新
