---
name: 張獻元 周二/周三 入院 cathlab keyin 改手動
description: 張獻元在週二/週三 admission 的 cathlab 排程規則複雜（同日 vs N+1 取決於 H 註記是否含王思翰/張倉惟、bed 條件、AM/PM 限制等），自動 keyin 容易錯。改成「列清單提醒使用者，使用者手動 key」。
type: feedback
---

**規則：** 入院日為**週二**或**週三**且醫師為**張獻元**的病人，**不要**自動 cathlab keyin，改成：

1. 把這些病人列清單提醒使用者（病人姓名、病歷號、F/G、H 註記）
2. 使用者自己進 WEBCVIS 手動 key
3. 其他醫師、其他日期照常自動 keyin

**Why:**
- 張獻元週二/週三的 cathlab 排法有多重交織規則：
  - 週二 admit + H 無王思翰/張倉惟 → 同日 PM (張獻元週二 PM H2)
  - 週二 admit + H 含王思翰/張倉惟 → N+1 (張獻元週三 AM/PM C2)
  - 週三 admit → 同日（張獻元週三 AM C2 / PM C2）；週四無時段不走 N+1
  - 12C / 1B / 床位限制、AM 無法提前等個案細節
- 即使 verify_cathlab.py 有同日規則 sample，實務上仍有手動例外（如 `feedback_zhang_xianyuan_same_day.md`、`feedback_zhang_xianyuan_wed_same_day.md`、`feedback_xianyuan_wed_mistake.md`）
- 2026-04-27 4/28 admit case：陳麗花/王得福/陳中坤 預期同日 PM 但被自動 key 到 4/29，事後修補成本高（不能刪舊 entry）→ 使用者明示改手動

**How to apply:**
1. 建 cathlab JSON 時，先 filter 掉「主治醫師=張獻元 AND 入院日 weekday ∈ {Tue, Wed}」的 row
2. 在最後 cathlab keyin 流程結束前，列出這批被 filter 的病人清單，標題如「張獻元周二/周三 — 請手動 key」
3. 不要嘗試自動排時段或建議 cathlab 日期，避免誤導
4. `admission-cathlab-keyin` skill 已記錄此規則
5. 其他 weekday（週四/週五/週日/週一）的張獻元病人照常 auto-keyin

**已知實例：**
- 2026-04-27 4/28(Tue) admit：張獻元 8 位中 3 位 (陳麗花/王得福/陳中坤) 被誤排 4/29，使用者明訂「以後張獻元周二周三都不要 key，提醒我就好」
