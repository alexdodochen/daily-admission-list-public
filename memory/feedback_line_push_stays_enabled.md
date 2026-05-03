---
name: LINE 推播私有照常跑 — public 撤文件 ≠ 關功能
description: 移除 public repo 的 LINE 文件不等於停 LINE 推播；私有環境每天 07:50 cron-job.org 仍照常觸發 bot 推到成醫-心內群組，不要叫使用者去 disable cron job
type: feedback
---

兩件事獨立，不要搞混：

1. **Public mirror 不顯示 LINE infra 細節**（doc-level；已 2026-05-03 完成）
   - 步驟五從工作流程 txt 拿掉、bot URL/endpoint 移到 `_*` gitignored
   - 目的：別的行政總醫師 clone public 看不到我私有的 bot 架構

2. **LINE 推播功能本身在私有環境照常跑**（runtime-level；不要動）
   - cron-job.org 4 個 job（07:50 入院序推播 / 07:55 備援 / 週六版 ×2）**保持 enable**
   - Render bot service 維持線上
   - 使用者依賴每天 07:50 自動推到「成醫-心內」群組給住服

**Why（2026-05-03 踩過）：**
我做完 (1) 之後在 HANDOFF 跟使用者建議「Pending Action #1: 去 cron-job.org 把 4 個 LINE 推播 job stop」— 使用者立刻反駁「我還是需要私有repo有這個功能啊!!」。差點把使用者每天用的功能整個關掉。

**How to apply:**
- 任何「拿掉 public LINE 文件 / scrub bot infra」的工作 → 只動 doc，不動 cron job、不動 Render bot
- 不要在 HANDOFF / 對話中建議「停 cron job」「disable bot」這類話
- 使用者明確說「這功能我不要了」才動 runtime；單純的 doc-level scrub 不要連帶觸發 runtime 動作
- 提到 LINE 推播現況時，明確區分「文件層」vs「實際運作」
