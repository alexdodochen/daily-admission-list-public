---
name: 當週入院 JSON 保留至下週一
description: emr_data_*.json / cathlab_patients_*.json 當週(週日-週五)產出的，workflow-docs 不可刪，下週一才清
type: feedback
---

規則：`emr_data_*.json` / `cathlab_patients_*.json` 等入院清單 JSON 在 `/workflow-docs` 跑 cleanup 時，**當週(週日到週五)產出的不刪**，留給使用者後續調動病人時可以重讀舊 JSON 加速省 token。**隔週週一**才刪掉上週批次。

**當週定義**：週日（Sun）到週五（Fri）。週六不屬於任一週（介於兩週之間）。

**算法**：
```python
from datetime import date, timedelta
today = date.today()
# weekday: Mon=0..Fri=4, Sat=5, Sun=6
week_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
# 從檔名 YYYYMMDD or MMDD 解析 file_date
# 保留條件：file_date >= week_sunday
```

**Why:** 使用者在週中常會調動病人到鄰近日期（如 5/4 的某病人改到 5/5）。若 workflow-docs 在週中或週末把當週的 emr_data_*.json 刪掉，下次調動就要重 fetch EMR — 浪費 EMR session、浪費 token、浪費 Claude 處理時間。當週舊 JSON 保留可以直接讀回 EMR 內容、F/G、子表格資料，節省整個 round-trip。

**How to apply:**
- workflow-docs Step 5 cleanup 時：對 `emr_data_YYYYMMDD.json` / `cathlab_patients_YYYYMMDD.json` 解析檔名日期
- 比對 `week_sunday`：日期 ≥ week_sunday 的就保留
- 隔週週一（next Mon）跑 cleanup 時，上週 Sun-Fri 已不在當週範圍 → 自然會被刪
- 用 `_*` 底線前綴 scratch / debug 檔不適用此規則（仍照原規則 > 3 天可刪）
