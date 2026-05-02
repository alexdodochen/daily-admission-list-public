---
name: 陳則瑋住院 + 劉秉彥門診 → cathlab second VS = 劉秉彥
description: 陳則瑋的住院病人若 OPD 平常看劉秉彥，cathlab keyin 必須放劉秉彥為 attendingdoctor2
type: feedback
---
陳則瑋住院病人，cathlab keyin 時：
- 主刀 (attendingdoctor) = 陳則瑋
- 第二刀 (attendingdoctor2) = **劉秉彥**（前提：該病人 OPD 是看劉秉彥門診）

判斷依據：EMR 子表格 C 欄（EMR 內容）開頭【EMR來源門診：(門診)YYYY/MM/DD 劉秉彥 一般內科XX診】或 EMR 內容註明「(非本醫師門診)」且原醫師為劉秉彥。

**Why：** 規則由使用者於 2026-05-02 提出。劉秉彥常 refer 病人給陳則瑋住院做 cath，第二刀掛上他名字較合宜（行政/責任歸屬）。

**How to apply：**
- `cathlab_patients_YYYYMMDD.json` 若 attending=陳則瑋 且 EMR 來源門診=劉秉彥 → `second=劉秉彥`
- 已 keyin 過的舊資料若需回頭補：用 cathlab_keyin.py UPT 階段加 attendingdoctor2
- 例：5/4 黃茂盛（陳則瑋 / 劉秉彥門診 refer）→ second=劉秉彥
- 與「兩位 second」規則（feedback_cathlab_third_doctor.md）獨立——這條就是補預設第二刀，不涉及 third
