---
name: cp950 亂碼時不可用猜的名字回覆
description: Windows cp950 終端輸出中文變成亂碼時，必須改用 UTF-8 檔案再讀回，絕不可憑記憶/推測中文名字回報給使用者
type: feedback
---

當 Python 腳本的 stdout 在 Windows cp950 終端輸出中文，顯示為亂碼（例如 `��@�E ����� (02632333)`）時，**絕對不可以靠上下文或記憶猜測中文名字**回報給使用者。必須：

1. 在執行腳本時加 `PYTHONIOENCODING=utf-8`（bash `PYTHONIOENCODING=utf-8 python ...` 或 script 內 `sys.stdout.reconfigure(encoding='utf-8')`）
2. 搭配 `> file.txt 2>&1` 導向到 UTF-8 檔案
3. 用 Read tool 讀回該檔案看到真正的中文
4. 再用正確名字回答使用者

**Why:** 使用者 2026-04-22 驗 cathlab 時，我從亂碼 `��@�E ����� (02632333)` 猜成「陳柏偉 黃忠海」等一堆錯誤名字（實際是「陳柏偉 黃忠海」只是少數對，其他如「葉立浩 林南」完全是我瞎編）。使用者回「你的名字怎麼都怪怪的」我才發現。醫療場景名字亂猜的風險非常高 — 誤會病人身分直接影響排程。

**How to apply:**
- **任何時候** Python 腳本印出的中文呈現亂碼，立刻停下，改走 UTF-8 file 流程再報告
- 不要假裝讀得懂或從 context 推測 — 寧可多跑一次腳本，不要誤導使用者
- 常見症狀：`��` / `�E` / `�i` 等替代字元堆疊
- 相關：CLAUDE.md Environment 段已提 `encoding='utf-8'` 要明寫；stdout redirect 另需 `PYTHONIOENCODING=utf-8` 環境變數
