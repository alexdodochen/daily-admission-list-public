---
name: 張獻元週三入院排同日PM導管
description: 張獻元週三入院的病人一律排當日週三PM導管（C2），不走 N+1
type: feedback
---

張獻元 週三入院 的病人全部排 **同日週三 PM** 導管（張獻元週三自己的 C2 時段）。

**Why:** 張獻元週三 AM C2 + PM C2 都有時段、週三 PM 沒有 borrow 例外（不像週二 PM H2 會被王思翰/張倉惟借走）。使用者 2026-04-22（週三）明確指示 `獻元周三入院都排週三PM導管`。

**How to apply:**
- `verify_cathlab.py`：wd==2（Wed）且 doctor=='張獻元' → cath = 同日（不加 borrow check）
- cathlab keyin：張獻元週三入院患者時段排 `YYYY-MM-DD 13:00` 起（PM C2 房間）
- 入院序 N-V 的 U 欄「預計心導管」會是入院同日，不是 N+1
- 類比既有規則：週二同日 PM H2（有 borrow 例外）、週五同日、廖瑀週一 AM H2 若有晨會另行處理
- 僅適用 **張獻元本人為主治醫師** 的 row；其他醫師週三入院仍走 N+1

現有相關規則（對照）：
- 週五入院 → 同日（`CLAUDE.md` rule 5）
- 張獻元週二入院（無 王思翰/張倉惟）→ 同日 PM（`verify_cathlab.py` wd==1）
- 新：張獻元週三入院 → 同日 PM（`verify_cathlab.py` wd==2）
