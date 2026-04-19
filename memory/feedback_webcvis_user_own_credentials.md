---
name: WEBCVIS 帳密由各使用者自填
description: 本地 app 的 WEBCVIS 登入欄位每位使用者填自己的帳密，不提供預設值
type: feedback
---

啟動 / 設定本地入院清單 app（`public_daily_admission_app`）時，WEBCVIS 的 `cathlab_user` / `cathlab_pass` 欄位**留空，由使用者自行輸入自己的院內帳密**。

**Why:** `107614/107614` 是 user 本人的帳號，其他使用者拿去登入會在 WEBCVIS 留下「是 user 在操作」的稽核紀錄，等於盜用身份。App 設計初衷是「每個人用自己的 LLM 帳號 + 自己的憑證」，WEBCVIS 同理。

**How to apply:**
- 介紹 app 設定步驟時，WEBCVIS 那格只寫「自己的院內帳密」，**不要**填任何預設值或範例帳號。
- 同規則延伸：LINE token、LLM API key 也一樣 — 各人的就是各人的，不要在 UI 或說明文件放別人的 key。
- 這只限 WEBCVIS **登入帳密**。其他不屬個人身份的靜態資源（Sheet ID、服務帳號 JSON 路徑、EMR/WEBCVIS base URL）可以共用或提供預設值。
