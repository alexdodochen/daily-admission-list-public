---
name: EMR 擷取範圍規則（SOAP only，截斷於 [Medicine]）
description: C 欄存完整 SOAP、D 欄存四段式摘要，兩者都截斷於 [Medicine]，不含藥品/檢驗/掛號
type: feedback
---

EMR 寫入 Sheet 的兩個欄位：
- **C 欄 (EMR)**：完整 SOAP note 原文（門診 header + [Diagnosis] + [Subjective] + [Objective] + [Assessment & Plan]），**截斷於 `[Medicine]`**
- **D 欄 (EMR摘要)**：四段式摘要（一、診斷 二、病史 三、客觀檢查 四、本次住院計畫），也從截斷過的 SOAP 取得

**兩欄都不能含以下內容**：
- `[Medicine]` 之後的任何內容
- `[Plan : 依類別]`
- `-------藥品-------`、`-------檢驗-------`、`-------其他-------` section
- 慢性處方箋、檢驗單、掛號、住院許可

**HTML 擷取 vs 純文字擷取**：
- HTML 擷取：只讀 `<div class="small">`（含 SOAP markers），略過 `iportlet-content`/`plan`/`medicine`
- 純文字擷取（innerText）：找第一個 `[Medicine]` 或 `-------` 出現位置，前面全保留、後面全丟

**Why:** 藥品/檢驗/掛號不是臨床評估內容，會造成 EMR 欄位冗長、摘要被干擾，user 2026-04-13 明確要求清掉。

**How to apply:** 不論用 Playwright innerText 或 HTML parse，寫入 Sheet 前都要截斷。STOPS 清單：`['[Medicine]', '[Medication]', '[Plan : 依類別]', '-------藥品', '-------檢驗', '-------其他', '------']`。
