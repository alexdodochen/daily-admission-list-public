---
name: 入院名單推播只傳N-Q四欄
description: LINE推播入院名單只傳序號、主治醫師、病人姓名、備註(住服)四欄
type: feedback
originSessionId: 633be95c-833c-4ae9-b22a-177136f43e81
---
LINE 入院名單推播只傳 N-Q 四欄：序號、主治醫師、病人姓名、備註(住服)。

**Why:** 住服只需要這四欄資訊，不需要病歷號、術前診斷等內部資料。

**How to apply:** `admission_push.py` 的 `read_admission_list` 只讀這四欄，`format_admission_message` 只輸出這四欄。備註讀的是 Q 欄「備註(住服)」，不是 R 欄「備註」。
