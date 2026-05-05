============================================
  交班文件 — Last Updated: 2026-05-05 17:30
============================================

【本次 session 做了什麼】
  1. 設置 PostToolUse hook (scripts/post_sheet_format_check.py + .claude/settings.json) — 偵測 process_emr/generate_ordering/rebuild_date_sheet/refresh_emr.py + YYYYMMDD 自動跑 enforce_sheet_format
  2. 重啟改期功能：5/5 admit 18 人中 10 人改期 → V 標記 + 主資料 + 子表格 rebuild + 5/6 cathlab DEL/ADD
     - 5/5 sheet: 10 人 V 欄寫上目標日期 (5/12 王樹英, 5/12 楊瑪露, 5/6 蘇正勝, 5/7 其他 7 人)
     - 5/6 sheet: 蘇正勝 + 黃睦翔 sub-table 新增
     - 5/7 sheet: 7 人 + 詹世鴻(6人)/陳儒逸(4人) rebuild + 陳柏偉 placeholder
     - 5/12 sheet: 王樹英+楊瑪露 + 張獻元 sub-table 新增
  3. cathlab DEL+ADD: 10 ADD 全部 verify OK (5/7 H2/5/8 C1/C2/5/13 C2)；DEL 自動化失敗，使用者手動處理 7 筆
  4. enforce_sheet_format 跑 5/5/5/6/5/7/5/12/5/10/5/11/5/13/5/14 — 都 OK
  5. CLAUDE.md rule 5 更新（reschedule 雙 mode：V flag only / 完整搬遷）

【當前狀態】
  - Branch: main, 工作樹 dirty (待 commit:
      .claude/settings.json
      scripts/post_sheet_format_check.py
      cathlab_patients_reschedule.json
      memory/feedback_webcvis_del_manual.md
      memory/feedback_reschedule_active.md
      memory/reference_post_sheet_format_hook.md
      memory/MEMORY.md
      memory/HANDOFF.md
      CLAUDE.md)
  - Hook 不在本 session 生效 — 下次啟動或 /hooks 重載才會
  - WEBCVIS：5/6 16 人，5/7 16 人，5/8 16 人，5/13 3 人 — 全部 verify OK

【下一步該做什麼】
  - 5/7 sub-table 陳柏偉 → 潘美香 (chart 15282032) 重抓 EMR：`python process_emr.py 20260507`（之前 rebuild 中途 429 損失 EMR/F/G 資料，目前 H 欄寫「[EMR/F/G need refetch — script crash]」）
  - 5/11+ 下週入院清單截圖（等使用者送）
  - （仍待）memory 全英化 batch、public mirror sheet `1u2FZE6...` PHI 清除

【已知問題 / 卡關】
  - WEBCVIS account 107614 沒 DEL 權限（自動化嘗試 v1 form-direct submit + v2 force-enable button click 都失敗）。新 memory: feedback_webcvis_del_manual.md
  - cathlab_keyin.py 沒 DEL 功能（只 ADD/UPT）。如要自動化 DEL 需另開 script + 解決帳號權限
  - sub-table rebuild 大規模 write 易碰 429 quota（5/7 第一次跑 4 個 block 中途死於 quota，第 4 block 陳柏偉 損失資料）。緩解：batch_write_cells、time.sleep(2.0+)、超過一定 patient 數可拆兩 session

【不要重蹈覆轍】
  - **find_main_end 不能只看 blank row**：sub-table title 也在 col A 有值，naive scan 會回傳錯誤 main_end（5/12 do_5_12 第 1 版踩過）→ 改用 YYYY-MM-DD regex（gsheet_utils.enforce_sheet_format 範本）
  - **sub-table rebuild 要先 capture ALL existing blocks**（不只目標醫師那塊）— 不然 unrelated doctor 資料被 clear 後消失，rebuild 又只重畫 captured 的 blocks（5/7 陳柏偉 case：原本是因為 capture OK 但 rebuild 中途 quota 死於第 4 block）
  - **WEBCVIS DEL 直接 form submit 不會生效**（buttonName=DEL 被 server 默默丟棄）— 不要再嘗試自動化 DEL
  - **改期完整搬遷需使用者明確授權** — 不要看到 V 欄就自動移 sheet。預設仍是「V flag only」mode
  - **enforce_sheet_format 在 hook 中跑** vs 手動跑：hook 只在 4 個指定腳本後跑，手動跑（如本次 5/10-14）需 `python -c "from gsheet_utils import enforce_sheet_format; ..."`

【相關檔案】
  - 程式碼新增：scripts/post_sheet_format_check.py
  - 設定新增：.claude/settings.json
  - JSON：cathlab_patients_reschedule.json (10 人 ADD source of truth)
  - 規則更新：CLAUDE.md (rule 5 reschedule 雙 mode)
  - sheets 動到：20260505 / 20260506 / 20260507 / 20260512（全部 enforce_sheet_format OK）

【重要 memory 檔（本 session 新增/更新）】
  - feedback_webcvis_del_manual.md (新)
  - feedback_reschedule_active.md (新)
  - reference_post_sheet_format_hook.md (新)
  - MEMORY.md (索引同步)
