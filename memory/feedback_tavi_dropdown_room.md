---
name: TAVI 在預計心導管下拉清單，cathlab 排程選開刀房
description: TAVI 是合法的 G/U 欄值（不需放 H/R 註記），cathlab keyin 時 examroom 選「外科開刀房25房」
type: feedback
---

TAVI 在 `下拉選單!D9`（預計心導管），是正式選項：
- **子表 G 欄 / N-W U 欄** → 直接填 `TAVI`，**不要**塞到 H 註記或 R 備註
- **WEBCVIS cathlab keyin**：
  - `phcjson` ID = `PHC20170406095551`（已在 `cathlab_id_maps.json`）
  - `examroom` 選 `xa-外科開刀房25房`（不是 H1/H2/C1/C2）

**Why:** 過去誤以為 TAVI 不在下拉清單，把它填到 H 註記，導致 cathlab keyin 時 phcjson 為空，需要事後手動補。實際上 TAVI 是 dropdown 既有選項，地點走外科開刀房而非心導管室。

**How to apply:**
- EMR 預填 G 欄時，看到 TAVI 直接填入 G（不要 fallback 到 H）
- `cathlab keyin` 腳本 ROOM_CODES 需新增：`"開刀房": "xa-外科開刀房25房"`（或讓 TAVI 自動 map 到此房）
- `feedback_cathlab_note_fallback.md`「不在選單則填註記」的規則對 TAVI **不適用**
