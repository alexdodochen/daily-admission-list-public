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

**Current reminders** (as of 2026-04-08):
- W01: Combined Meeting 安排 (Sat-Wed, weekly cycle)
- W02: 借床 (Mon-Fri, daily, /trigger-bed)
- W03: 排下周入院序 (Thu-Sun, weekly cycle)
- W04: 傳排程給 EP/PPM (Mon-Fri, daily, /trigger-schedule)
- W05: Combined Meeting VS出席 (Mon-Tue, daily, /trigger-combined) — 需在 cron-job.org 設定 `0 14 * * 1,2` Asia/Taipei
