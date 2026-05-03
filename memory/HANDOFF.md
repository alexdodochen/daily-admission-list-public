============================================
  交班文件 — Last Updated: 2026-05-03 afternoon
============================================

【本次 session 做了什麼】
  1. Public mirror 結構性硬化：私有 SHEET_ID 從所有 tracked 檔案撤除（7+ 處），LINE 推播 infra 三份 reference memory + 工作流程步驟五全部移到 `_*` gitignored
  2. 部署 push-time 護欄：`scripts/pre_push_check.py` + `.githooks/pre-push` 掃禁忌字串（私有 SHEET_ID / bot URL / endpoint / PEM private key），命中即擋；setup `git config core.hooksPath .githooks` 已執行
  3. 工作流程 txt 由 7 步縮為 6 步（刪步驟五 LINE 推播；步驟六/七 → 五/六）
  4. 新增 `memory/_private_setup.md`（gitignored）集中私有 SHEET_ID + bot URL + 跨機器 setup 指引
  5. 驗證 git history 0 筆 PEM private key（service account JSON 內容從沒進 commit）→ 接受不做歷史 rewrite

【當前狀態】
  - Branch: main, working tree clean
  - 最新 commit: f343d05 (docs: clarify — public doc scrub ≠ disable LINE feature)
  - origin/main 已同步（私有 + public 兩邊都成功 push，3 個 commit）
  - pre-push hook 在這台機器已啟用（`git config core.hooksPath` = `.githooks`）
  - 結束 session 後 user 要求關閉 terminal

【下一步該做什麼】
  - 其他 clone 機器（OPD / 別台）首次工作前各跑一次 `git config core.hooksPath .githooks`
  - 跨機器 setup：`scp local_config.py` + service account JSON + `memory/_private_setup.md` 到新機器（這份 gitignored 不會自動同步）

【LINE 推播注意：私有照常跑！】
  - cron-job.org 那 4 個 job（入院序推播 / 備援 / 週六版 ×2）**繼續啟用**，私有環境每天 07:50 照常推到「成醫-心內」群組
  - 此 session 只做了「public mirror 文件不顯示 bot infra」，**沒有**動 cron-job.org / Render bot / 推播實際運作
  - 千萬不要建議使用者停 cron job —— 會把使用者每天用的功能整個關掉

【已知問題 / 卡關】
  - public mirror sheet `1u2FZE6...` 仍殘留 5/3 真實病人 PHI（使用者尚未授權清理 — 5/1 殘留問題）
  - 5/4 (Mon) 起 emr_data_2026042x / cathlab_patients_20260429 等上週 JSON 才能依 workflow-docs 規則清掉（今天是 5/3 Sun，差一天）
  - admission-cathlab-keyin SKILL.md 仍未實作週掃描程式碼（只在文件加 HARD RULE）— pending from prev session

【不要重蹈覆轍】
  - **任何 LINE / private SHEET_ID / bot infra → 寫到 `_*.md` 或 `_*.txt`**（gitignored）。寫進 tracked 檔案 → pre-push hook 擋下；不要用 `--no-verify` 繞
  - pre_push_check.py 自己加 regex 時不能寫死字面值（會自己擋自己；用抽象描述 + 引用 _ 檔）
  - LINE bot 讀私有 sheet（這 repo 動不到 bot 配置）→ 「公開 sheet 永遠不會被推播」是結構性事實，不必特別處理
  - service account JSON `sigma-sector-...json` 一直在 .gitignore；歷史驗證沒進過 commit（不需要 history rewrite）

【相關檔案】
  - scripts/pre_push_check.py（新，禁忌字串 regex list）
  - .githooks/pre-push（新，git hook）
  - memory/_private_setup.md（新，gitignored，私有值集中）
  - _step5_line_push.md（新，gitignored，LINE 推播工作流程備存）
  - memory/_reference_line_reminder_bot.md / _reference_line_monthly_quota.md / _reference_cronjob_render_gotchas.md（rename 加 _ 前綴；本機可讀）
  - memory/feedback_no_line_in_public.md（新）
  - memory/project_public_mirror_sync.md（更新：加 LINE 不存在 + push 護欄段落）
  - CLAUDE.md（加「Public 不能有的東西」HARD RULE 段落）
  - 每日入院清單工作流程.txt（步驟五刪除 + 重編號）
  - .gitignore（加 `_*.md` pattern）

【重要 memory 檔（本 session 新增/更新）】
  - feedback_no_line_in_public.md（新）
  - project_public_mirror_sync.md（更新）
  - feedback_local_config_required.md（更新：references _private_setup.md）
  - feedback_all_data_to_google_sheet.md（scrub 私有 SHEET_ID）
  - reference_machine_python_path.md（scrub 私有 SHEET_ID）
  - MEMORY.md（索引 +1 條，刪 2 條 broken entries）
