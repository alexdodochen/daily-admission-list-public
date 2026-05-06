---
name: 不可自行觸發LINE推播
description: 絕對不可以自己觸發LINE群組推播，必須等使用者明確指示
type: feedback
originSessionId: 633be95c-833c-4ae9-b22a-177136f43e81
---
不可自行觸發 LINE 推播到成醫-心內群組。

**Why:** 使用者明確要求不要自己觸發推播，推播內容會直接發到真實的LINE群組，影響所有成員。

**How to apply:** 任何涉及 LINE 推播 trigger endpoint（清單見 gitignored `memory/_reference_line_reminder_bot.md`）的操作，都必須等使用者明確說「推播」或「觸發」後才執行。修改程式碼可以，但不要自己打 endpoint。
