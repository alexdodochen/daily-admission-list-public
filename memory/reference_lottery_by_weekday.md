---
name: reference_lottery_by_weekday
description: 抽籤表（主治醫師抽籤表）各日（Mon-Fri）有時段醫師清單快照 + *2 加註，lottery 對照用，避免靠 schedule_readable.txt 猜
type: reference
originSessionId: a237e859-cb18-4efd-8aa5-0e8ae104bf8e
---
# 主治醫師抽籤表 — by weekday（snapshot 2026-04-26）

**權威來源**：Google Sheet `1DTIRNy10Tx3GfhuFq46Eu2_4J74Z3ZiIh7ymZtetZUI` 工作表 `主治醫師抽籤表`，col A-E = 週一至週五。

**每次 lottery 仍要直讀 sheet**（見 `feedback_lottery_read_full_column.md`）；此檔僅作離線對照、避免重蹈把非時段醫師當時段醫師的覆轍（4/24 session 我把張獻元/劉嚴文誤當週一時段醫師被使用者糾正）。

## 各日時段醫師清單

| 日 | 時段醫師（`*2` = 2 支籤） |
|---|---|
| 週一 (col A) | 陳柏升、許志新、詹世鴻、李柏增*2、陳昭佑、廖瑀、黃鼎鈞、陳柏偉 |
| 週二 (col B) | 劉嚴文、陳昭佑、李柏增、陳儒逸、鄭朝允、劉秉彥、陳則瑋、張獻元、黃鼎鈞、黃睦翔 |
| 週三 (col C) | 詹世鴻*2、林佳凌、陳儒逸、張獻元*2、黃睦翔、廖瑀 |
| 週四 (col D) | 陳柏升、許志新、林佳凌、陳柏偉、黃鼎鈞*2、柯呈諭*2、黃睦翔 |
| 週五 (col E) | 劉嚴文、陳柏偉、陳儒逸、~~詹世鴻~~、李文煌、柯呈諭、鄭朝允、陳則瑋 |

## 入院日 → 抽籤欄對應

| 入院日 | 抽籤依據 | 欄 |
|---|---|---|
| 日 | 隔日週一 | A |
| 一 | 隔日週二 | B |
| 二 | 隔日週三 | C |
| 三 | 隔日週四 | D |
| 四 | 隔日週五 | E |
| 五 | **當日週五**（週六無抽籤表） | E |
| 六 | 通常無入院 | — |

## 例外（CLAUDE.md rule #16, #5）

- **詹世鴻 週五入院** → 強制視為**非時段醫師**，從 pool 中移除（即使 col E 列出他）。cathlab 也走非時段（H1 2100+, note="本日無時段"）。上表 col E 已用刪除線標記。
- **張獻元 週三入院** → 同日 PM C2，不走 N+1（CLAUDE.md rule #5 例外）。仍進週三 lottery pool（*2）。

## 維護

- Sheet 異動後（如新進主治、退休、輪調）→ 直接更新本表
- 此 snapshot 可能落後實際 sheet → lottery 永遠以 sheet 直讀為準，本檔僅交叉驗證
