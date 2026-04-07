---
name: 導管排程不在選單的項目填入備註欄
description: 預計心導管若不在WEBCVIS下拉選單中（如Cardioversion），改填入note欄位
type: feedback
---

若預計心導管的值不在 WEBCVIS 系統的 phcjson 選項樹中，將該值填入備註欄（`input[name="note"]`）而非留空。

**Why:** 使用者仍需要在排程系統中看到該資訊，備註欄是自由文字，不受選單限制。
**How to apply:** keyin 時先查 proc_map，找不到 ID 就把 procedure 值寫入 note 欄位。
