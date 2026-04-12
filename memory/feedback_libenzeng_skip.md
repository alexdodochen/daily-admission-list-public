---
name: 李柏增 2026/08 前不 key-in 排程
description: 202608 之前，李柏增不填入主刀/第二主刀醫師欄位（cathlab keyin 時直接略過）
type: feedback
---

**2026/08 之前**，李柏增 (105146) 不要 key 進 WEBCVIS 的主刀或第二主刀醫師欄位。即使時段表寫「陳昭佑(李柏增)」或「EP(李柏增)」等，也只填第一主刀，attendingdoctor2 留空。

**Why:** 使用者明確指示。之前已在 `feedback_cathlab_keyin_flow.md` 提到「李柏增不填入主刀/第二主刀醫師欄位」，但沒寫時限；補上「2026/08 前」這個條件方便 2026/08 後恢復。本次 4/14 李亨利 keyin 時誤填 李柏增 為第二醫師，已 UPT 清空。

**How to apply:**
- cathlab_keyin_*.py 腳本的 PATIENTS 資料，`second` 欄位若原本是「李柏增」→ 直接改 `None`
- 時段表括號內若出現「李柏增」，該欄位略過
- 2026/08/01 後此規則失效，屆時需重新確認
- 其他第二醫師（葉建寬寬、葉立浩浩、洪晨惠晨、許毓軨齡、蘇奕嘉嘉）照舊 keyin
