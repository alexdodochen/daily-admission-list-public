============================================
  交班文件 — Last Updated: 2026-05-02 night
============================================

【本次 session 做了什麼】
  1. 5/4 入院 11 人完整流程：image diff-update（B/K 補齊）→ N-V 11 列 ordering（含 康李金春 用 黃睦翔 round-in 排第 8 位）→ cathlab keyin（5/5 共 9 ADD 成功）
  2. 三條新規則寫死進 memory + skills：
     - cathlab ADD 前**必掃整週 (Mon-Fri)**，已存任何一天 → STOP 不自動 ADD（5/2 踩坑：康李金春 5/6 CRT 已排，被誤 ADD 5/5 H1 2100）
     - 寫 N-V 前**必當下重讀子表格 F/G/H**（HARD）— 不可用 session 早期 cached 值（5/2 踩坑：8/11 病人 F/G/H 寫錯）
     - 陳則瑋住院 + 劉秉彥門診 → cathlab attendingdoctor2 預設 劉秉彥（限劉秉彥）
  3. local_config.py 補建（這台機器之前缺，session start CLAUDE.md 第 2 步）

【當前狀態】
  - Branch: main, working tree 動了（cathlab_patients_20260504.json + memory/* + skills/* 待 commit）
  - 最新 commit: a5c5199
  - 5/4 sheet：N-V 11 列正確、子表格 F/G/H 完整、enforce_sheet_format 通過
  - 5/5 cathlab WEBCVIS：10 人正確（含 鄭法榮 NEW ADD），唯 康李金春 多了一筆 5/5 H1 2100 錯排程

【下一步該做什麼】
  - **使用者手動進 WEBCVIS DEL 康李金春 5/5 H1 2100 廖瑀 那筆**（5/6 H1 1430 那筆才是真實 CRT）
  - 5/3 (Sun) 07:50 cron 自動推 5/4 N-Q 4 欄到 LINE 住服群
  - 5/5 (Tue) 起入院 image 來時走標準流程；先記得套用「ADD 前掃週」規則

【已知問題 / 卡關】
  - 黃茂盛 5/4 cathlab second 沒補劉秉彥（user 選 3.b 不回頭補），下次有陳則瑋住院+劉秉彥門診的 case 才正式套規則
  - public mirror sheet `1u2FZE6...` 仍殘留 5/3 真實病人 PHI（使用者尚未授權清理 — 5/1 殘留）
  - admission-cathlab-keyin SKILL.md 仍未實作週掃描程式碼（只在文件加 HARD RULE），下次需修 cathlab_keyin.py 加 week-scan phase 0

【不要重蹈覆轍】
  - cathlab keyin 之前**先用 playwright 跑週掃描（Mon-Fri）**，list 所有 hit chart no，從 JSON 移除已存在的 → 才呼叫 cathlab_keyin.py
  - 寫 N-V 之前 **gspread 即時重讀 sub-table F/G/H**（即使 30 秒前才讀過）— 使用者會在 EMR/format check 之間手動修
  - 陳則瑋住院病人 EMR C 欄寫「(門診)... 劉秉彥 ...」→ JSON `second=劉秉彥`
  - 黃嬌子 H="不用排導管 要排CTV ... 入院檢查" → SKIP cathlab keyin
  - 跨機器 session start：先 git fetch + ls local_config.py + check-previous-progress

【相關檔案】
  - cathlab_patients_20260504.json（10 entries：陳威豪/王薪詠/黃茂盛/高艷秋/李淑眞/林怡昌/郭清波/鄭法榮/陳麗花/康李金春；黃嬌子 skip）
  - .claude/skills/admission-cathlab-keyin/SKILL.md（加 HARD RULE 5：ADD 前掃整週）
  - .claude/skills/admission-ordering/SKILL.md（加 HARD RULE：寫 N-V 前重讀子表格）
  - memory/feedback_cathlab_week_check_before_keyin.md（新）
  - memory/feedback_chen_zewei_liu_bingyan_second.md（新）
  - memory/feedback_subtable_H_to_R_ordering.md（更新 — 升級為 hard rule + 5/2 案例）

【重要 memory 檔（本 session 新增/更新）】
  - feedback_cathlab_week_check_before_keyin.md（新）
  - feedback_chen_zewei_liu_bingyan_second.md（新）
  - feedback_subtable_H_to_R_ordering.md（更新）
  - MEMORY.md（索引 +2 條）
