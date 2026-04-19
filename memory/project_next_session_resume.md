---
name: 下次開機要先處理的事
description: 2026-04-20 session 結束時的 pending 進度 — 下次開 session 優先提醒使用者
type: project
---

## 下次開 session 第一件事：**主動提醒使用者以下進度**

使用者 2026-04-20 夜休前明確要求「下次提醒我進度」。`check-previous-progress` 跑完後，除了常規報告，**要額外在第一則回覆列出以下 pending items**：

### Phase 8 exe 打包 — 差最後 2 步就能發 exe

1. **實跑 PyInstaller 測試** — `packaging.spec` / `BUILD.md` / `HANDOFF.md` 都已就位，需要：
   - `cp <真實 SA>.json app/bundled/service_account.json`
   - `pyinstaller packaging.spec --noconfirm`
   - 在乾淨 Windows 驗證：設定頁顯示「系統預設 ✓」、跑完 Step 1-6
2. **Chromium 首次下載邏輯** — 首次啟動偵測 `playwright install chromium` 有無跑過，沒跑過提示/自動跑

### 本次 session 新產出（待 push 並記得）

- `public_daily_admission_app/HANDOFF.md` — 4 個雲端資源（GCP/Sheet/GitHub/LINE）年度交接 checklist，目的讓「原開發者離職也能被接手」
- 架構決定：兩個 repo 分工
  - `public_daily_admission_app`（公開）→ exe 跑的 FastAPI code，updater 從這抓
  - `daily-admission-list`（私人）→ CLI scripts + memory + 工作流程
- 結論：使用者選 **GUI 路線傳承**（不走 CLI + 自建 Sheet），因為行政總醫師非技術背景

**Why:** 使用者明確說「下次提醒我進度」，代表 memory 不只是 passively 讀取，要**主動播報** Phase 8 還差什麼才能發 exe。

**How to apply:**
- Session 開頭 `check-previous-progress` 的「Where we left off」段落**必須**包含上述 2 個 pending items
- 看到使用者說「繼續 Phase 8」/「發 exe」/「打包」等關鍵字 → 直接進入上述步驟
- 當 PyInstaller 跑成功 + Chromium 邏輯做完 → 更新 `project_webapp_phase8_exe.md` 劃掉該項，並**刪掉這份 resume 檔**（避免久放過期）
