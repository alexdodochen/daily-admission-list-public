============================================
  交班文件 — Last Updated: 2026-05-04 14:15
============================================

【本次 session 做了什麼】
  1. **EMR 摘要功能整個拿掉**：sub-table 從 8 欄 (A-H) → 7 欄 (A-G)；D=EMR摘要 整欄移除，E-H 全部左移成 D-G。process_emr.py 不再呼叫 generate_summary()，只寫 C (raw EMR) + E (術前診斷) + F (預計心導管)。F/G 自動判讀邏輯保留，因本來就讀 raw EMR。
  2. 修了 6 個 .py + 4 個 skill + 工作流程 txt + 專案 CLAUDE.md（新增 rule #22）。新增 `memory/feedback_no_emr_summary.md`，更新 MEMORY.md 索引（順手把舊 H 欄 ref 一條改成 G 欄）。
  3. 全域 CLAUDE.md (`C:\Users\dr\.claude\CLAUDE.md`) 重寫成英文主幹 + 加 reply-language 段（中文回覆 + 台灣醫學晶晶體可），整體 < 1000 token。專案 CLAUDE.md 使用者自己已順手精簡為英文版（不要回退）。
  4. 修了 admission-cathlab-keyin / admission-format-check 內幾條漏改的 H/F/G col ref + A:H ref（pre 5/4 殘留）。

【當前狀態】
  - Branch: main，working tree clean (HANDOFF 時間戳更新後再次 dirty 是正常)
  - 最新 commit: a824e14 `feat: drop EMR summary, sub-table 8→7 cols`
  - 私有 + public mirror 都已 push 成功
  - 程式碼 syntax OK + pre_push_check.py 過
  - 公開 mirror 結構性護欄保持有效（pre-push hook + dual push routing）

【下一步該做什麼】
  - **memory 全英化 batch**：使用者要求把 CLAUDE.md / memory 主體改英文（晶晶體醫學詞 + user quote 保中文）；工作流程 txt 維持中文（user 自己維護）。約 50+ memory 檔，建議下個 session 開新 task 處理
  - 本週 5/4-5/8 sheet：使用者命令再跑 admission-image-to-excel（已清理上週 JSON、保留本週/下週的 emr_data + cathlab_patients）

【已知問題 / 卡關】
  - 舊 sheet (5/3 之前) 仍是 8 欄 layout — 使用者選 α 不 migrate；新版 verify_cathlab / generate_ordering / process_emr 跑舊 sheet 會抓錯欄。預期不會回頭跑（那週已 cathlab 完）
  - 還有約 10 個 memory 檔仍寫舊 col ref (F=術前診斷 / G=預計心導管 / H=註記 / D=EMR摘要)。canonical source 是新 `feedback_no_emr_summary.md`，其他檔將來讀到時若有衝突以新檔為準。完整翻譯留給「memory 全英化」batch 一起做
  - public mirror sheet `1u2FZE6...` 5/3 真實病人 PHI 仍未清（從 5/1 留下）

【不要重蹈覆轍】
  - **動到子表格 col index 一律用 7 欄假設**（`r[:7]`、`endColumnIndex=7`、`A:G`）。看到 8/A:H 都是 5/4 前死碼
  - **N-V 寫入前必當下重讀子表格 E/F/G**（不是 F/G/H — CLAUDE.md rule #18 已更新）
  - **process_emr.py 寫 sub-table 用 E{row}/F{row}**（不是 F{row}/G{row}）
  - 全域 CLAUDE.md 已改英文主幹 — **回覆 user 仍中文**，文件本體保持英文
  - LINE / 私有 SHEET_ID 一律寫 gitignored `_*.md`（pre-push hook 會擋）
  - 圖→Sheet 完成就停，不跨 step 自動連跑（feedback_no_auto_lottery.md）

【相關檔案】
  - 程式碼：gsheet_utils.py / process_emr.py / generate_ordering.py / verify_cathlab.py / rebuild_date_sheet.py / emr_toggle_script.js
  - Skills：.claude/skills/admission-{lottery,ordering,emr-extraction,format-check,cathlab-keyin}.md
  - 文件：每日入院清單工作流程.txt, CLAUDE.md (project), C:\Users\dr\.claude\CLAUDE.md (global)

【重要 memory 檔（本 session 新增/更新）】
  - feedback_no_emr_summary.md（新，canonical post 5/4 column shift 規則）
  - feedback_subtable_H_to_R_ordering.md（更新：H→G col shift 警示）
  - feedback_post_edit_format_check.md（更新：sub-table A:H→A:G、子 header 拿掉 EMR摘要）
  - MEMORY.md（索引 +1 條 + 順手修一條 H→G）
