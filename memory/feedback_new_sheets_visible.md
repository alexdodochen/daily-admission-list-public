---
name: 新建日期 sheet 不要隱藏
description: rebuild / duplicate template 建立的新 date sheet 必須 hidden=false，使用者要立刻看得到
type: feedback
---

`rebuild_date_sheet.py`（以及任何用 `duplicateSheet` 從 template 建新 date sheet 的 path）建出來的 sheet **必須顯式 set `hidden=false`**。

**Why:** `duplicateSheet` 會繼承來源 sheet 的 `hidden` 屬性。Template `20260417`（以及大多數舊 date sheet）為了 tab 列乾淨都被使用者隱藏了 → 所有用它當 template 複製出來的新 date sheet 也預設 hidden=true → 使用者打開試算表看不到，要展開「隱藏的工作表」才找得到，很煩。5/4 user 一次抓 5 天（5/10-5/14）後立刻提醒：「新增的工作表不要自動隱藏 要顯示出來」。

**How to apply:**
- `rebuild_one()` 在 `duplicateSheet` 後馬上加一個 `updateSheetProperties` request：

```python
sh.batch_update({'requests': [{
    'updateSheetProperties': {
        'properties': {'sheetId': ws.id, 'hidden': False},
        'fields': 'hidden',
    }
}]})
```

- 可以併進 step 2 的 batch（appendDimension / unmerge / clear）一起 send，不浪費 API call
- 任何其他從 template 複製建新 date sheet 的 path（手動 duplicate、新 helper script）都要遵守
