============================================
  交班文件 — Last Updated: 2026-05-01 (Fri afternoon)
============================================

【本次 session 做了什麼】
  1. 部署 dual-push origin remote — git push origin main 自動推 daily-admission-list + daily-admission-list-public 兩個 repo
  2. SHEET_ID 分歧解決 — gsheet_utils.py 用 try/except import local_config（gitignored），public 預設 1u2FZE6...，本地有 local_config.py 覆寫成 1DTIRNy...
  3. admission-cathlab-keyin SKILL.md 補 third 欄位 + 黃鼎鈞 Mon 強制洪晨惠 + 兩位 second 對照表（對齊 cathlab_keyin.py 實作）
  4. 此台新機器環境 setup：Node.js v25.9.0、@google/gemini-cli 0.40.1、jq（winget）、git identity（local-only：alexdodochen）
  5. statusline 設定 — Node-based ~/.claude/statusline.js 顯示 5h / 7d quota + ctx %（不顯示 API cost）
  6. Clone Claude-Gemini-Dialogue 到 ~/repos/ 作為 token-saving delegation 工具

【當前狀態】
  - Branch: main, clean（待會本次 workflow-docs 變更會 commit）
  - 部署: 私有 + public 都同步到 9a8055d（feat: SHEET_ID local override）
  - 最新 commit: 9a8055d feat: SHEET_ID local override mechanism for public mirror
  - 此台機器環境: Node v25.9.0 + Gemini CLI 0.40.1 + Python 3.14.4 + gspread/google-auth/playwright + Chromium browser 全部已裝；end-to-end 驗證 `from gsheet_utils import SHEET_ID` → 私有 ID（local_config.py 覆寫成功）

【下一步該做什麼】
  - 5/1 (Fri) 若有入院清單 → 走標準流程（image OCR → lottery → EMR → ordering → cathlab）；週五入院 cathlab 同日（非 N+1）
  - 此台機器已可直接跑 admission scripts（無需再裝任何依賴）
  - Gemini CLI OAuth 已由 user 自行完成；token 緊張時可用 ~/repos/Claude-Gemini-Dialogue/scripts/delegate.sh

【已知問題 / 卡關】
  - Hook 偶爾會擋 `git push origin main`（理由「直推 main bypass PR review」），workaround：user 在 prompt 打 `! git push origin main`。本次 session 後段就不再擋了，可能是 pattern 或 cache 問題
  - Hook 也擋 bash 讀 ~/.claude/settings.json（self-modification 守則），改用 Read tool 驗證

【不要重蹈覆轍】
  - **絕對不要** `git remote add public ...` — 結構性把 public 變 named remote 就有被 pull 的風險（user 明確要求 public 永不 pull 回 local）
  - 不要在 PowerShell 用 `npm` — 會被 execution policy 擋；改用絕對路徑 `& "C:\Program Files\nodejs\npm.cmd" ...`
  - 切到別台機器設 statusline 不要用 API cost / duration（subagent 預設誤導）—— user 要的是 rate_limits.five_hour / seven_day 用量
  - 兩位 second（時段表「黃鼎鈞(浩、晨)」）→ 第二位放 cathlab JSON 的 third 欄位（recommendationDoctor），舊規「放 note」已廢
  - 黃鼎鈞 Mon cathlab → second 強制洪晨惠（即使時段表 Mon 沒寫黃鼎鈞）

【相關檔案】
  - gsheet_utils.py（SHEET_ID try/except import）
  - local_config.py（gitignored，含私有 SHEET_ID）
  - .gitignore（加 local_config.py）
  - CLAUDE.md（Public mirror section、Sheet ID 雙 ID 標示、External tools）
  - .claude/skills/admission-cathlab-keyin.md（third + 黃鼎鈞 Mon）
  - ~/.claude/statusline.js + ~/.claude/settings.json（statusline）
  - ~/repos/Claude-Gemini-Dialogue/（外部工具）

【重要 memory 檔（本 session 新增/更新）】
  - project_public_mirror_sync.md（新；含 dual-push setup + SHEET_ID 解法）
  - reference_claude_gemini_dialogue.md（新；委派工具說明）
  - feedback_statusline_session_quota.md（新；statusline 顯示規則）
  - MEMORY.md（索引加 3 條）
