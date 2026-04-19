---
name: Keyin 資料來源以子表格為準
description: 所有 cathlab keyin / verify 的病人清單、術前診斷、預計心導管一律從子表格（統整資料）讀取，不從 N-V 入院序
type: feedback
---

**所有要 key 入 WEBCVIS 的資料，一律從子表格（統整資料，即主治醫師病人清單）讀取**，不要從 N-V 入院序欄位讀。

**Why:** N-V 入院序是「要給住服的入院順序清單」，是子表格的子集。有些病人（已預先排程、無時段醫師、pre-scheduled 個案）不會被放進 N-V，但**仍然需要 cathlab 排程**。過去依賴 N-V 做 verify / keyin 會漏掉這些病人。

本次 (2026-04-12 session) 的漏單事件：
- 4/14 入院 sub-table 有 16 人，N-V 入院序只有 10 人
- 差的 6 人中，3 人已被他人排入其他天（05002006、04762762、13786017）
- 但另 3 人確實沒排：10680953 陳許黃焿（張獻元 PAOD/PTA）、00748681 孫建源（黃睦翔 CAD/PCI）、17098226 吳巧楹（林佳凌 無資料）
- 另外 01884136 謝好 的 N-V 顯示 STEMI/PCI 與 sub-table 的 CAD/LHC 不一致，以 sub-table 為準

**How to apply:**
1. `verify_cathlab.py` 應改讀子表格而非 N-V
2. cathlab_keyin_* 的 PATIENTS 清單來源要從子表格 parse
3. 若 N-V 和子表格的 F/G 欄（術前診斷/預計心導管）不一致，**以子表格為準**
4. 子表格包含了所有要做 cathlab 的病人，這才是完整清單
