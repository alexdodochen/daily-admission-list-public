---
name: cron-job.org + Render free tier 運作與陷阱
description: 免費版 timeout 30s 上限、連續失敗自動停用、Render 15 分鐘閒置 spin-down、cron-job.org 單一 keep-alive 不可靠需 UptimeRobot 雙保險
type: reference
---

## cron-job.org（免費版）限制

- **Timeout 上限 30 秒** — 在 ADVANCED 頁設 > 30 會被退回 "The maximum timeout is 30 seconds"
- **自動停用**：連續失敗約 24 次 → job 的 Next execution 變 `Inactive`。必須回 edit 頁把 "Enable job" toggle 切回 ON + SAVE 才會恢復
- **通知預設全 OFF**：在 COMMON 頁最下方 "Notify me when..." 區塊，有三個 toggle。至少開前兩個：
  - `execution of the cronjob fails`
  - `the cronjob will be disabled because of too many failures`
- **無 retry**（付費才有）— 所以本專案用「備援 job」：同 URL 的第 2/3 次觸發排在主 job 後 5 / 10 分鐘，當手動重試

## Render free tier 行為

- **閒置 15 分鐘 spin-down** — 沒收到 HTTP 請求就 SIGTERM worker
- **Cold start 可能 > 30 秒** → cron-job.org 30s timeout 不夠 → 503 → 連鎖失敗 → keep-alive 被自動停用 → 服務永睡（2026-04-16 實例：18:06 PM spin-down，22:10 PM keep-alive 被停，服務睡到隔天 08:07 AM 才被 Claude 手動 /health ping 叫醒）
- **手動恢復**：任何 HTTP 請求都能冷啟（只要 client 肯等）。`curl` 或瀏覽器打 `/health` 都行

## cron-job.org 單一 keep-alive 不可靠（2026-04-17 實戰教訓）

即使 Keep Alive 每 5 分鐘打一次，仍可能發生長時間停機：
- **2026-04-17 16:00~17:01 PM** 服務睡了 1 小時。cron-job.org 4:45/4:50/4:55 三次 /health 都回 503（< 1s fast fail，Render edge 直接擋，沒觸發 cold boot）。Render logs 在這整段空白，意思是 request 根本沒到 app。
- 可能原因：Render 對同 IP (cron-job.org) 頻繁 request 的 rate limit / edge drop，或 spin-down 後的 cooldown window 拒絕 boot
- 相同 5-min 間隔打進去，有時過有時不過，不可預期

**Fix: 加第二個 keep-alive 從不同 IP 打**（Cost: 0）
- **UptimeRobot** 免費版 5 分鐘間隔，不同 IP source
- 兩邊同時每 5 分鐘打 /health → 就算一邊 edge 被擋，另一邊會過
- UptimeRobot 設定：Monitor Type=HTTP(s), URL=/health, Interval=5 min

## line-reminder-bot 目前配置（2026-04-17 雙保險後）

- Dashboard (cron-job.org): <https://console.cron-job.org/jobs>
- Dashboard (UptimeRobot): <https://dashboard.uptimerobot.com/monitors>
- 服務 URL: `https://line-reminder-bot-wvwo.onrender.com`
- Keep Alive #1: cron-job.org `/health` 每 **5 分鐘**
- Keep Alive #2: UptimeRobot `/health` 每 **5 分鐘**（不同 IP，雙保險）
- 全部 15 個 cron-job.org job 都已開啟 `fails` + `auto-disabled` 通知

## 收到 disabled email 的恢復 SOP

1. 登入 cron-job.org → 點該 job → EDIT
2. COMMON tab → "Enable job" toggle 切 ON
3. SAVE
4. 若服務也掛了：瀏覽器打 `/health` 等 30–60 秒冷啟一次，之後 keep-alive 接手

## Playwright 操作技巧（future reference）

- Edit URL: `https://console.cron-job.org/jobs/<job_id>`
- MUI switch: `<label>` 內包 `<input type=checkbox>`，用 `label:has-text('...') input[type=checkbox]` + `.is_checked()` 判斷，label click 切換
- Timeout 欄: `div.MuiTextField-root:has(label:has-text('Timeout')) input`
- 畫面較高（排程+通知+save）→ 設 viewport 2000px 以上比較好截圖
