---
name: Session 結束清除暫存檔
description: workflow-docs 盤點時必須清除 _* scratch、emr_data_*、cathlab_keyin_* 等暫存檔，不留到下個 session
type: feedback
originSessionId: f7c7a3b6-f16d-4c80-8c96-967ab8ba3fbe
---
workflow-docs 盤點（/workflow-docs）最後一步必須清除專案中的暫存檔案。

**Why:** 暫存檔會隨 session 累積到上百個，佔空間且降低目視辨識效率。這些檔案在工作進行中有用，但 session 結束後就是垃圾。

**How to apply:** 在 workflow-docs 的階段 4.5 執行，刪除以下 pattern：
- `_*.py` / `_*.txt` / `_*.json` / `_*.png` / `_*.log`
- `emr_data_*.json`
- `cathlab_keyin_*.py`
- `cathlab_*_final.png` / `cathlab_error_*.png`

永久模組（`gsheet_utils.py`、`fetch_emr.py` 等）、設定檔、memory 目錄絕不刪除。
