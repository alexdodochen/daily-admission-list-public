============================================
  交班文件 — Last Updated: 2026-05-01 evening
============================================

【本次 session 做了什麼】
  1. 5/3 入院 8 人 N-V ordering 完成（黃鼎鈞 #1, 黃睦翔 #2, 廖瑀, 詹世鴻, 鄭朝允, 黃鼎鈞, 詹世鴻, 詹世鴻）
  2. 這台機器 Python 3.14 + service account JSON 環境補齊（winget 裝 + user 貼 JSON）
  3. Lottery 規則澄清：明確序數（#1, #2）= 跨組 override；模糊「然後 X」= 預設規則 — `feedback_lottery_roundrobin.md` 已重寫
  4. 新增 `reference_machine_python_path.md` 記錄各機器 python 位置 + WindowsApps stub 陷阱 + hookify python3 不兼容

【當前狀態】
  - Branch: main, working tree 動了 (CLAUDE.md, memory/* 待 commit)
  - 最新 commit: cc52528 (workflow-docs sync — 4/29 那次)
  - 5/3 sheet N-V 已寫入並 enforce_sheet_format 完成

【下一步該做什麼】
  - 5/4 (Mon)、5/5 (Tue)、5/6 (Wed)、5/7 (Thu) 已有 cathlab_patients JSON，等對應入院日 image 來時走標準流程
  - 5/3 cathlab keyin（5/4 那批）若還沒做：`python cathlab_keyin.py cathlab_patients_20260503.json`（已驗證 4/29 pre-session 完成過 5/3-5/7 全 35 entries）

【已知問題 / 卡關】
  - 這台機器 PATH 沒含 Python，要用絕對路徑 `C:\Users\user\AppData\Local\Programs\Python\Python314\python.exe`；想永久解決可加 PATH 或 disable hookify plugin
  - hookify plugin 啟著但 0 條規則，且 `python3` 在 Windows 不存在 → 每次 Stop event 吐 cosmetic error

【不要重蹈覆轍】
  - Lottery 看到「黃鼎鈞 #1, 黃睦翔 #2」這種**明確序數**就是跨組 override，可把非時段醫師擺到時段中間；只有「然後是 X」這種模糊講法才回去問或保守按預設規則
  - 跨機器 service account JSON 不會 git sync（gitignored）— 新機器要 user 手貼或 USB 帶
  - WindowsApps `python.exe` 是 0-byte stub，silent fail；要先確認真 python 路徑

【相關檔案】
  - memory/feedback_lottery_roundrobin.md（規則重寫）
  - memory/reference_machine_python_path.md（新）
  - CLAUDE.md（加跨機器 setup 引用）

【重要 memory 檔（本 session 新增/更新）】
  - feedback_lottery_roundrobin.md（重寫：兩段 RR + 跨組 override 規則）
  - reference_machine_python_path.md（新）
  - MEMORY.md（索引更新 1 條）
