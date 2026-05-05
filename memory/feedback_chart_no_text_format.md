---
name: 病歷號必須以文字格式寫入
description: N-V ordering 的 S 欄（病歷號）和主資料 I 欄必須是 TEXT 格式，否則前導 0 會被 Google Sheets 吃掉
type: feedback
originSessionId: 726bb693-3593-4f39-838b-e29a5122e8cb
---
病歷號固定 8 碼且常含前導 0（例：01283084、04669716、06077539）。寫入 Google Sheet 時必須：

1. **numberFormat 設 TEXT**：`repeatCell` 下 `{"userEnteredFormat": {"numberFormat": {"type": "TEXT"}}}`
2. **值用 stringValue 寫入**：透過 `updateCells` + `userEnteredValue: {stringValue: ...}`，**不要**用 `ws.update()` 配 `USER_ENTERED`（會被解析成數字）

**Why**: 使用者 2026-04-21 抓到 4/22 N-V 重寫時 S 欄前導 0 消失。`ws.update(..., value_input_option='USER_ENTERED')` 寫字串 '06077539' 會被 Sheets 轉成 6077539。

**How to apply**: 任何寫入病歷號的地方（主資料 I 欄、N-V 的 S 欄、子表格 B 欄），都要同時下 numberFormat TEXT + stringValue，不要只寫值。`write_doctor_table` 和 `generate_ordering.py` 已處理主資料＋子表格，但直接 `ws.update()` 寫 N-V 的 path 要自己做。
