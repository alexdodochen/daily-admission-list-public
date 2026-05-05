---
name: feedback_one_sheet_per_distribution_day
description: 每日入院清單截圖 = 該日「送出的」清單；col A 即使顯示多個 admit 日期也全歸該日 sheet，絕不依 admit 日期拆 sheet
type: feedback
originSessionId: a237e859-cb18-4efd-8aa5-0e8ae104bf8e
---
「{MMDD} 入院清單」= **{MMDD} 那天送出的清單**，整張歸 `2026MMDD` sheet，不管 col A（實際住院日）是不是 MMDD 或 MMDD+1/+2。週末/週日 sheet 常常含 5/3、5/4、5/5 多日 admits 因為週末一次給整批未來幾天的入院。

**Why:** 2026-04-26 session 處理 5/3 截圖時我看到 col A 有 5/3 / 5/4 / 5/5 三種日期，自作聰明只把 4 個 5/3 admits 寫入 20260503 sheet、認為 5/4 / 5/5 admits 屬另外的 sheet。使用者糾正：8 人全部歸 20260503 sheet。

**How to apply:**
- 收到「{MMDD} 入院清單」截圖 → 整張寫入 `2026MMDD` sheet，不依 col A 拆
- 不要主動問「5/4 / 5/5 admits 要不要建另外 sheet」— 那些日期之後另外有自己的清單會送出
- 若 col A 全部都是同一天，當然也歸該日 sheet，沒矛盾
- 唯一例外：使用者明確說「這張同時涵蓋 X/Y 多日，請拆 sheet」才拆
