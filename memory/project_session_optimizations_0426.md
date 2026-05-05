---
name: project_session_optimizations_0426
description: 2026-04-26 build 出 cathlab_keyin.py 通用版 + batch_write_cells helper + admission-diff-update skill，取代手刻 per-date 雜活，預估 -75% token / -60% wall-time
type: project
originSessionId: a237e859-cb18-4efd-8aa5-0e8ae104bf8e
---
2026-04-26 session 完成三件 token/速度優化（取代每天手刻 200 行 per-date scratch）：

1. **`cathlab_keyin.py`** — 通用 cathlab keyin driver，吃 `cathlab_patients_*.json`。取代每天複製 200 行 `_cathlab_keyin_MMDD.py`。ID maps 從 `cathlab_id_maps.json` 載。
2. **`gsheet_utils.batch_write_cells(updates)`** — 一次 API call 推多個 cell/range，取代 write→sleep→write 循環。減 gspread quota + 加速 sheet 寫入。
3. **`.claude/skills/admission-diff-update.md`** — 新 skill，封裝「圖片更新已存在的日期 sheet」流程（病歷號 PK / 三向 diff / batch update / 子表格 + N-V 連動 / EMR 只重跑新增）。

**Why:** 同類 session（diff-update + cathlab keyin）今天耗 ~33k 變動 token，新工具預估 ~7.5k，省 75%。Wall-time 從 ~30 分縮到 ~10 分。

**How to apply:**
- 下次有圖片更新已存在 sheet → 走 `admission-diff-update` skill，不要再手刻 `_diff_update_MMDD.py`
- 下次 cathlab keyin → 寫一個 `cathlab_patients_YYYYMMDD.json` (3-10 行) 然後 `python cathlab_keyin.py <json>`，不要再每天複製 keyin 腳本
- 多個 sheet cell 改動 → 用 `batch_write_cells` 一次推完，不要逐 cell `write_range` + sleep
- 第一次 cathlab 用 generic 版若 ID 缺 → 報錯，補進 `cathlab_id_maps.json` 永久解（見 `feedback_cathlab_id_maps_only.md`）
