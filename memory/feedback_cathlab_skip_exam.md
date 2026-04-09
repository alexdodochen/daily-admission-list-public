---
name: 導管排程跳過檢查病人
description: 備註含「檢查」的病人不排導管；第二醫師多人時葉立浩優先key，其餘放備註
type: feedback
---

**規則 1：備註含「檢查」→ 不排導管**
如果病人備註中出現「檢查」（如「入院檢查貧血」），該病人不需 key 入導管排程。
注意：「非導管床」、「HF AE」等不一定跳過，只有明確含「檢查」字眼才跳過。

**規則 2：第二醫師多人時 → 葉立浩優先 key，其餘放備註**
例如「黃鼎鈞(浩、晨)」：
- attendingdoctor2 填 葉立浩（105430）
- 備註加「晨」或「洪晨惠」

**Why:** WEBCVIS attendingdoctor2 只能填一位，需要固定優先順序
**How to apply:** cathlab keyin 時，second doctor 永遠先填葉立浩，其他第二醫師名放 note 欄
