============================================
  交班文件 — Last Updated: 2026-04-29 night
============================================

【本次 session 做了什麼】
  1. 4/29 入院 8 人 N-V ordering（高艷秋取消已刪），cathlab 7 人 keyin（陳信義 HF AE skip）
  2. 5/3-5/7 入院 35 人 cathlab keyin（5/4-5/8 cathlab 共 35 entries 全 verify OK）
  3. cathlab_keyin.py 加 `third` 欄位（recommendationDoctor 推薦醫師），ADD + UPT 都支援
  4. 三條新規則寫進 repo + memory：
     - session-start 必先 git fetch（CLAUDE.md）
     - 張獻元週三入院 lottery/ordering 視為非時段（cathlab 仍同日 PM C2）
     - 兩位 second → 第二位放 recommendationDoctor（取代舊「放 note」），黃鼎鈞 Mon 強制 second=洪晨惠
  5. Skills GitHub sync — 4 SKILL.md 更新 + 2 新 skill (audit-oe-skill, euroscore-workflow) 上傳

【當前狀態】
  - Branch: main, clean
  - 最新 commit: da989aa (cathlab third doctor + 5/3-5/7 patients)
  - WEBCVIS: 4/29 (4/30/5/4-5/8) cathlab 排程全 verify OK

【下一步該做什麼】
  - 4/30 (Thu) 起的入院清單來時走標準流程（image OCR → lottery → EMR → ordering → cathlab）
  - admission-cathlab-keyin SKILL.md 還是舊版描述（手動 JS 操作），不符實作 cathlab_keyin.py — 待重寫

【已知問題 / 卡關】
  - 5/3 黃鼎鈞「全麻 LAAO+PFA Varipulse」「全麻 PFA Affera」實際可能要等結構日，目前先排 5/4 N+1 H1 2100+ 非時段，user 可指示改 date
  - 5/3 劉廖寶蓮 H="5/5 MTEER" → 排到 5/5 H2 1800（非黃睦翔結構日 Wed/Thu，照 H 指定）
  - admission-cathlab-keyin SKILL.md vs 實作脫節（未影響運作但描述過時）

【不要重蹈覆轍】
  - **必先 git fetch** 才動手（CLAUDE.md Session start 已寫死）—— 4/29 踩過坑（用舊版 keyin 倒退陳中坤 CAD→Unstable，靠新版 _normalize_diag 自動修回）
  - cathlab_patients_YYYYMMDD.json 可能 origin 已有，不要重寫；用對方版本
  - 「Others:XXX」走 _resolve_diag_id 自動 fallback PDI20090908120008，不要手動加 cathlab_id_maps.json entry
  - 黃鼎鈞 Mon cathlab → second=洪晨惠（即使時段表看似 Mon 無時段）
  - 兩位 second → 第二位 third 欄位（recommendationDoctor），不是 note

【相關檔案】
  - cathlab_keyin.py（加 `third` 欄位）
  - CLAUDE.md（rule 15 改寫 + Session start git fetch）
  - 每日入院清單工作流程.txt（cathlab JSON schema 加 third、第二醫師規則 update）
  - cathlab_patients_2026050X.json (3-7) 已 commit
  - https://github.com/alexdodochen/claude-skills push 到 c18a0c6（4 updates + 2 新 skill）

【重要 memory 檔（本 session 新增/更新）】
  - feedback_cathlab_third_doctor.md (新)
  - feedback_zhang_xianyuan_wed_lottery.md (新)
  - feedback_cathlab_times.md (更新 — 連續 +1 分鐘規則)
  - MEMORY.md (索引更新 2 條)
