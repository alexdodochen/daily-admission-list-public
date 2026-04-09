---
name: LINE Reminder Bot repo
description: Private GitHub repo for LINE automated reminders — repo location, architecture, and how to add new reminders
type: reference
---

**Repo**: `alexdodochen/line-reminder-bot` (private), cloned at `C:\Users\OPD\Desktop\Fellow 資料夾\line-reminder-bot`

**Architecture**: Flask app on Render (free tier), cron-job.org triggers HTTP endpoints, Upstash Redis for completion state.

**How to add a new reminder**:
1. `reminders.py` — add entry to `WEEKLY_REMINDERS` (daily cycle: `trigger_weekdays` + `message`; weekly cycle: `cycle_start_weekday` + `steps`)
2. `app.py` — add `/trigger-xxx` endpoint calling `send_by_id('W0x')`
3. cron-job.org — set schedule hitting the new endpoint with `?secret=TRIGGER_SECRET`
4. Push to main → Render auto-deploys

**Admission push** (as of 2026-04-09):
- `/trigger-admission`: 每日 07:50 推播當日入院序到成醫-心內群組（skip_if_sent=True 避免重複）
- `/trigger-admission-weekend`: **週六 07:50** 找當日之後第一個有 Sheet 的日期推播（Redis dedup，7天TTL）
- 訊息格式：N-Q 四欄（序號/主治醫師/病人姓名/備註(住服)），不含病歷號
- cron-job.org: `50 7 * * 6` Asia/Taipei → `/trigger-admission-weekend?secret=...`

**Current reminders** (as of 2026-04-09):
- W01: Combined Meeting 安排 (Sat-Wed, weekly cycle)
- W02: 借床 (Mon-Fri, daily, /trigger-bed)
- W03: 排下周入院序 (Thu-Sun, weekly cycle)
- W04: 傳排程給 EP/PPM (Mon-Fri, daily, /trigger-schedule)
- W05: Combined Meeting VS出席 (Mon-Tue, daily, /trigger-combined) — `0 14 * * 1,2` Asia/Taipei
