============================================
  交班文件 — Last Updated: 2026-05-01 night
============================================

【本次 session 做了什麼】
  1. 5/3 入院 9 人核對（image vs sheet）→ 補進賴左立(陳柏偉) 到 main row 10 + 陳柏偉 子表格
  2. 5/3 N-V 9 列 ordering 寫入私有 sheet — 最終順序：黃鼎鈞#1 吳宇豪、黃睦翔#2 劉廖寶蓮、黃鼎鈞#3 徐豐淇（user override #3 swap）、鄭朝允 陳吉忠、廖瑀 陳薏安、陳柏偉 賴左立、詹世鴻 周明仁/謝添福/吳峰欽
  3. verify_cathlab 確認 9 人全在 WEBCVIS（8 在 5/4 + 劉廖寶蓮 5/5 MTEER）
  4. MTEER 5/5 雙 booking 解釋 + 確認正常（xa-Hybrid2 介入 + xa-TEE 影像配套）
  5. 建好 `local_config.py`（這台機器之前缺，導致初次寫入跑到 public mirror）

【當前狀態】
  - Branch: main, working tree 動了 (CLAUDE.md, memory/* 待 commit)
  - 私有 sheet `1DTIR...` 5/3 N-V 為 9 列正確版本，enforce_sheet_format 完
  - public mirror sheet `1u2FZE6...` 仍有本次 session 初期誤寫的 5/3 真實病人資料 — **使用者尚未授權清理**
  - cathlab_patients_20260503.json 仍是 8 人版（缺賴左立），但 5/4 cathlab 已全部 keyin 完成（賴左立靠 verify_cathlab 確認在 5/4 的 14 筆內）

【下一步該做什麼】
  - 5/2 (Sat) 07:50 cron 自動推 5/3 N-Q 4 欄到 LINE — Q 欄目前全空（user 之前的 N-V 也都把住服 notes 放空，故保留）
  - 若使用者授權，清掉 public mirror sheet `1u2FZE6...` 的 5/3 主資料 + 子表格 + N-V（用 SHEET_ID 暫切 + batch_clear）
  - 5/4 (Mon)、5/5 (Tue)、5/6 (Wed)、5/7 (Thu) 入院 image 來時走標準流程（cathlab JSON 已有）

【已知問題 / 卡關】
  - public mirror sheet 殘留 5/3 真實病人 PHI — 等使用者點頭才清
  - hookify plugin Windows 不兼容（python3 不存在）— 沒解決，cosmetic error 持續

【不要重蹈覆轍】
  - **session start 必跑** `ls local_config.py`，沒有就建。fallback 到 public mirror = 把私有資料寫到公開 sheet
  - verify_cathlab.py 預設 N+1，遇 MTEER（5/5 而非 5/4）會 false-NG，要手動查後續日期
  - MTEER WEBCVIS 出現 2 筆是正常配套案，不要當重複處理

【相關檔案】
  - local_config.py（新建，gitignored）
  - memory/feedback_local_config_required.md（新）
  - memory/reference_mteer_double_booking.md（新）
  - CLAUDE.md（Session start 加第 2 步 local_config 檢查）

【重要 memory 檔（本 session 新增/更新）】
  - feedback_local_config_required.md（新）
  - reference_mteer_double_booking.md（新）
  - MEMORY.md（索引 +2）
