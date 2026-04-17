---
name: LINE Reminder Bot repo
description: Private GitHub repo for LINE automated reminders — repo location, architecture, endpoints, reminder list
type: reference
---

**Repo**: `alexdodochen/line-reminder-bot` (private). 本機（`C:\Users\dr`）**沒有 clone**，只有一份早期工作副本於 `C:\Users\dr\Downloads\Y\行政總醫師 claude\line_reminder_bot\`，**已落後部署版**（缺多個 endpoint），不要拿來當 reference。真正的開發/push 在另一台 `OPD` 機器。

**Architecture**: Flask app on Render (free tier), cron-job.org triggers HTTP endpoints, Upstash Redis for completion state.

**服務 URL**: `https://line-reminder-bot-wvwo.onrender.com`

**運維相關陷阱**: see `reference_cronjob_render_gotchas.md`（cron-job.org timeout/自動停用、Render spin-down、keep-alive SOP）

## 目前部署的 endpoints（從 Render logs 觀察到、非本地副本）

- `/health` — keep-alive
- `/webhook` / `/webhook-admission` — LINE webhook
- `/trigger` — 每日總檢查（8:00）
- `/trigger-bed` — 借床提醒（週一）
- `/trigger-admission` — 入院序推播（07:50 每日）
- `/trigger-admission-weekend` — 週六入院序推播
- `/trigger-schedule` — 傳排程給 EP/PPM
- `/trigger-waitlist` — 手動更新續等清單
- `/trigger-reschedule` — 聯絡病人改期
- `/trigger-combined` — Combined Meeting 倉惟思翰
- `/trigger-cath-reminder` — W05 Combined Meeting VS 出席

## 目前 cron-job.org 排程的 jobs（15 個，2026-04-17 快照）

| 時間 | 名稱 | endpoint |
|------|------|----------|
| 07:50 每日 | 入院序推播 | /trigger-admission |
| 07:50 六 | 週六入院序推播 | /trigger-admission-weekend |
| 07:55 每日 | 入院序推播 備援 | /trigger-admission |
| 07:55 六 | 週六入院序推播 備援 | /trigger-admission-weekend |
| 08:00 每日 | 每日提醒總檢查 | /trigger |
| 09:50/09:55/10:00 一 | W02 借床提醒 + 2 次備援 | /trigger-bed |
| 14:00 一二 | W05 Combined Meeting VS出席 | /trigger-cath-reminder |
| 16:00 二 | W06 倉惟思翰明天有導管 | /trigger-combined |
| 16:00 一 | W08 聯絡病人改期 | /trigger-reschedule |
| 17:30 一二三四 | W04 傳排程給 EP/PPM | /trigger-schedule |
| 17:30 一二三四 | W07 手動更新續等清單 | /trigger-waitlist |
| */5 min | Keep Alive | /health |

## 新增 reminder 的流程

1. `reminders.py` — 加入 `WEEKLY_REMINDERS` 條目（daily: `trigger_weekdays`+`message`；weekly: `cycle_start_weekday`+`steps`）
2. `app.py` — 加 `/trigger-xxx` endpoint 呼叫 `send_by_id('Wxx')`
3. cron-job.org — 排 job 打新 endpoint（帶 `?secret=TRIGGER_SECRET`），**記得開啟 fails / auto-disabled 通知**
4. Push 到 main → Render 自動部署

## 本地工作副本提醒

`C:\Users\dr\Downloads\Y\行政總醫師 claude\line_reminder_bot\` 是舊版副本（Apr 2026 初的 snapshot），跟 Render 上部署的不同。要看最新 code 只能：
- 登入 GitHub 看 `alexdodochen/line-reminder-bot`
- 或請使用者從 OPD 機器 pull/push
