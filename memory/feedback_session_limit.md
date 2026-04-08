---
name: Session Limit 管控
description: 每次 session 最多用 70% context，到達時停下通知使用者
type: feedback
---

每次 session 最多只能燒掉 70% 的 session limit。如果到達 threshold 還沒做完，就停下來通知使用者，等下一次 session 再繼續。

**Why:** 使用者希望控制 context 消耗，避免一次用完整個 session window
**How to apply:** 在大型實作任務中，持續監控 context 使用量，接近 70% 時停下並報告進度 + 下次繼續的指令
