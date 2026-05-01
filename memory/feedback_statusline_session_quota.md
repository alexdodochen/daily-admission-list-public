---
name: statusline 顯示訂閱方案 5h/7d quota，不要 API cost
description: 設 statusline 時要顯示 rate_limits.five_hour/seven_day.used_percentage 與 ctx %，不要顯示 API cost USD / API duration 那類給 console-only API 用戶看的指標
type: feedback
---

User uses Claude.ai 訂閱（Pro/Max），不是按量付費 API。statusline 要看的是 5 小時 session quota 用了幾趴，不是 API call 累計花了多少 USD。

## 規則

statusline 必顯示：
- `rate_limits.five_hour.used_percentage` → `5h X%`
- `rate_limits.five_hour.resets_at` → 倒數重置時間 `(1h59m)`
- `rate_limits.seven_day.used_percentage` → `7d X%`
- `context_window.used_percentage` → `ctx X%`

不要顯示：
- `cost.total_cost_usd`（USD 對訂閱用戶無意義）
- `cost.total_api_duration_ms`（同上）

## Why

- User 2026-05-01 明確糾正：「我不是要看API 我是要看我的五小時SEssion用了百分之幾那一類的資訊」
- 第一版誤把 statusline 寫成 API cost + duration（subagent 設計）
- 訂閱 quota 才是 user 真正關心的會不會撞牆

## How to apply

- 任何時候 user 要設定/重設/微調 statusline 都套這個規則
- 切到別台機器重設 statusline 也一樣（不要 default 回 API cost）
- 現有腳本：`~/.claude/statusline.js`（Node-based，已實作）；schema 來源 https://code.claude.com/docs/en/statusline

## 注意事項

`rate_limits` 只對 Claude.ai 訂閱用戶出現，且要 session 內有過至少一次 API response 後才會出現。新 session 第一句話前看不到 5h/7d 是正常的（不是 bug）。
