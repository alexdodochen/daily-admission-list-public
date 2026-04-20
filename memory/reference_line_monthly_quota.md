---
name: LINE Messaging API 月訊息配額（免費 200 則/月）
description: 免費 plan 每月 200 則上限，月底爆掉後所有 trigger 會回 500（LineBotApiError 429 "You have reached your monthly limit."）；月初 1 號 reset
type: reference
---

## 首次撞到：2026-04-19 23:50（4/20 早上所有 trigger 都 500）

Render logs 症狀：
```
LineBotApiError: status_code=429, error_response={"message": "You have reached your monthly limit."}
GET /trigger-admission?secret=... HTTP/1.1" 500 632
```

外部症狀：
- cron-job.org 所有 trigger 都「失敗（HTTP 錯誤）500」，response time 200ms–3s
- `/health` 與 `/webhook-admission` 照常 200（service 本身沒事，cron-job.org / Render / keep-alive 都正常）
- 上週五 16:00 W08 Friday reschedule 也 500（表示配額那時已經快用完）

## 免費 plan 限制

- **200 則/月**（Light plan 台幣約 800/月 5000 則；Stand/Pro 更多）
- 計月用的是**推送訊息（push message）**，不含被動回覆 webhook
- 重置日查 LINE Official Account Manager → 設定 → Messaging API → Monthly target limit

## 處理 SOP

1. 確認是 quota 爆（Render logs 搜 `monthly limit` 或 `status_code=429`）
2. 短期：等月初 reset
3. 中期：減量（合併提醒、週末不推、移除低價值提醒）
4. 長期：升級付費 plan

## 關聯

- reference_line_reminder_bot.md — 目前 cron-job.org 15 個 job 清單
- reference_cronjob_render_gotchas.md — 區分「cron/Render 問題」vs「這個 quota 問題」：前者 timeout/cold-start/自動停用；後者 500 但 response 很快
