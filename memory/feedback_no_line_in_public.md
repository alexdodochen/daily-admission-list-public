---
name: LINE / 私有 infra 一律寫 gitignored 檔
description: 未來新增 LINE 推播 / 私有 SHEET_ID / service account / bot infra 相關內容時，一律寫到 _*.md / _*.txt / memory/_*.md，禁止進入 tracked 檔案
type: feedback
---

未來在這個 repo 寫文件、memory、規則時，**任何**以下類別的內容**一律放在 gitignored 檔案**（root 的 `_*.md`/`_*.txt` 或 `memory/_*.md`），絕不能進入 tracked 檔案：

- 私有 SHEET_ID 字面值
- LINE 推播 bot 的 URL、endpoint 路徑、Bot ID、cron schedule、quota SOP
- Service account JSON 內容（PEM private key）
- 任何 bot/Render/cron-job.org 內部運維細節

**Why:**
- `origin push` 同時推到私有 + public mirror — tracked 檔案立刻 leak 給其他行政總醫師
- 使用者 2026-05-03 明確要求「之後我私有repo的更新 關於line的部分一律不推」「公用的不要有line功能」
- LINE bot 讀的是私有 sheet（public sheet 不會被推播是結構性事實），但 infra metadata 不該散播
- 已部署 `.githooks/pre-push` 護欄會擋常見違規字串，但寫之前自己先決定放哪裡，不要靠 hook 救

**How to apply:**
- 新增 LINE 規則 / bot 細節 → 寫到 `memory/_reference_line_reminder_bot.md` 或新建 `_*.md`
- 新增 setup 步驟提到私有值 → 寫到 `memory/_private_setup.md`
- 改既有 tracked 檔案前用 grep 確認沒帶入禁忌字串
- commit 前手動跑 `python scripts/pre_push_check.py` 雙保險
- 看到既有 tracked 檔案有遺漏的私有字串 → 立刻改成抽象描述 + 把字面值搬到對應 `_` 檔
- pre_push_check.py 自己寫 regex 描述時不能寫死字面值（否則自己擋自己）— 用 `<bot URL>`、「@-前綴」之類描述
