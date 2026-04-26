============================================
  交班文件 — Last Updated: 2026-04-26 night (long session)
============================================

【本次 session 做了什麼】
  1. 修兩個 skill (admission-lottery / admission-ordering) — 補 reference 引用 + weighted
     lottery + 兩段 RR 規則 (commit bcb9ca0, 65946de)
  2. 新建 cathlab_keyin.py 通用 driver + gsheet_utils.batch_write_cells helper
     + admission-diff-update skill (commit b2ccee2)
  3. 新建/補建 5 個 memory 檔（含 reference_lottery_by_weekday, feedback_cathlab_id_maps_only,
     project_session_optimizations_0426, feedback_one_sheet_per_distribution_day,
     feedback_ignore_op_date_default_n_plus_1, feedback_lottery_roundrobin）
  4. **跑 5 天入院清單 (5/3-5/7) 共 35 病人**：
     - 20260503: 8 人 (詹3/陳儒3 wait — 4 人；後加滿成 8)，N-V 排好
     - 20260504: 7 人，N-V 排好
     - 20260505: 8 人 (王樹英/楊瑪露 無資料)，N-V 排好
     - 20260506: 8 人 (黃秀琴 無資料)，N-V 排好
     - 20260507: 4 人 (柳美妍 無資料)，N-V 排好
  5. **三條重大規則寫進 repo**（CLAUDE.md / 工作流程 txt / admission-ordering.md）：
     - 一張截圖 = 一個 sheet（不依 col A 拆日）
     - 忽略開刀日 col B，cathlab 預設 N+1
     - N-V 兩段獨立 RR (時段→非時段)，組內 random.shuffle 不可借 sub-table 順序

【當前狀態】
  - Branch: main
  - 5 個 sheet (20260503-07) 主資料 + EMR + F/G 預填 + N-V 全部寫好
  - 4 個無資料病人 F/G 待使用者手動補
  - 最新 commit (待 push): 本 workflow-docs 的 docs sync

【下一步該做什麼】
  - **使用者審核 F/G**（特別 4 個無資料病人）並回覆要改的
  - 審核完 → cathlab keyin 5/4-5/8 (5 天) 用 cathlab_keyin.py + JSON
  - 4/28 黃秋煌 TTEER / 4/29 王陳玉英 改期由使用者手動

【已知問題 / 卡關】
  - MEMORY.md 索引 13 條指向不存在的 memory 檔（系統性，需逐條補建/刪除）：
    feedback_emr_html_parsing / feedback_emr_validation / feedback_no_data_patients /
    feedback_doctor_sharing_table / feedback_emr_manual_login / feedback_sheet_no_overwrite /
    feedback_waitlist_merge / feedback_diag_short_names / feedback_emr_auto_name_fix /
    feedback_cathlab_keyin_flow / feedback_nodata_still_keyin / reference_cathduration /
    feedback_zhang_xianyuan_wed_same_day
    （這些索引行寫的描述不夠詳細，補建時要靠記憶或 git log 重建內容）
  - admission-image-to-excel skill body 還在描述舊 xlsx 流程（描述行 OK），低優先

【不要重蹈覆轍】
  - 「{MMDD} 入院清單」= 一張截圖一個 sheet (`2026MMDD`)，不要依 col A 拆三日
  - 開刀日 (col B) 不可信，全部以 N+1 為預設
  - N-V 排序時不要把時段+非時段混在一起 RR — 必須兩段獨立
  - 組內 lottery 必須跑 `random.shuffle()`，**不可**借 sub-table 醫師出現順序當 lottery 結果
  - cathlab PDI/PHC ID 不要硬編，從 cathlab_id_maps.json 載
  - **規則寫私人 memory 還不夠，必須同步寫進 repo (CLAUDE.md / skill / 工作流程 txt)**
    才會跟著 repo 給其他使用者看到

【相關檔案（本 session 動到的）】
  - cathlab_keyin.py (新)
  - gsheet_utils.py (加 batch_write_cells)
  - .claude/skills/admission-diff-update.md (新)
  - .claude/skills/admission-cathlab-keyin.md (重寫，原 stub "404")
  - .claude/skills/admission-ordering.md (加兩段 RR + weighted lottery)
  - .claude/skills/admission-lottery.md (加 reference 引用)
  - CLAUDE.md (rule #2 改為兩段 RR；Key Files 區更新)
  - 每日入院清單工作流程.txt (步驟二/六更新；兩段 RR 範例)
  - _patients.py (5/3-5/7 各日依序覆蓋；最後 = 5/6+5/7)

【重要 memory 檔（本 session 新增/更新）】
  - feedback_one_sheet_per_distribution_day.md (新)
  - feedback_ignore_op_date_default_n_plus_1.md (新)
  - feedback_lottery_roundrobin.md (補建+更新，含 weighted lottery 範例)
  - feedback_cathlab_id_maps_only.md (新)
  - reference_lottery_by_weekday.md (補建)
  - project_session_optimizations_0426.md (新)
  - MEMORY.md (索引更新)
