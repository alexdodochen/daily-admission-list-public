---
name: 跨機器必先確認 local_config.py（否則寫到 public mirror）
description: gsheet_utils.SHEET_ID 預設是 public mirror，缺 local_config.py 時所有寫入會跑到公開 demo sheet
type: feedback
originSessionId: 5aa8a056-a465-471f-90a8-3b6720110bf5
---
新機器開工前，**先 `ls local_config.py`**。沒有就建：

```python
# local_config.py
SHEET_ID = '1DTIRNy10Tx3GfhuFq46Eu2_4J74Z3ZiIh7ymZtetZUI'
```

`gsheet_utils.py` 找不到 `local_config.py` → fallback 到預設 `1u2FZE6...`（public mirror demo sheet）。寫入時 silent succeed，使用者打開私有 sheet 會說「沒看到我做的更動」，再去發現是寫錯地方。

**Why（2026-05-01 踩過一次）：**
這台機器是新環境，`local_config.py` 沒建。我跑了 5/3 賴左立 補入 + 9 列 N-V ordering，全部寫到 public mirror。使用者：「我這邊做的更動都是要放私有sheet 不是public那邊!!」。public sheet 還因此被寫進真實病人 chart number / 姓名（PHI 暴露在公開 repo demo sheet）。

**How to apply：**
- session start 第一輪 git fetch + check-previous-progress 之後，**緊接著 `ls local_config.py`** 一次
- 沒有就 Write 一個（內容如上）
- 確認 `from gsheet_utils import SHEET_ID; print(SHEET_ID)` 開頭是 `1DTIR` 才開始寫入
- 任何 PII/PHI 寫入前的最後守門員
- 已寫到 public 的話 → 用 `batch_clear` 主動清掉 public 對應 sheet（不只是切回去就算了，公開 sheet 還在污染中）
