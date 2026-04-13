---
name: 導管排程 key-in 成功流程
description: WEBCVIS心導管排程自動化的完整技術流程，含表單欄位、ID映射、新增/修改方法
type: feedback
---

## 成功的 WEBCVIS 導管排程 key-in 流程

### 系統資訊
- URL: `http://cardiopacs01.hosp.ncku:8080/WEBCVIS/HCO/HCO1W001.do`
- 帳密: 107614 / 107614
- Form name: `HCO1WForm`

### 日期設定
daySelect1/daySelect2 是 readonly，必須先用 JS `removeAttribute('readonly')` 再設值（格式 `2026/04/08`）。

### 查詢 (QRY)
```js
document.HCO1WForm.buttonName.name = "QRY";
document.HCO1WForm.buttonName.value = "QRY";
document.HCO1WForm.submit();
```

### 新增 (ADD)
1. `page.click('input[name="patno2"]')` → 觸發 allclearid() 清空表單
2. `page.fill('input[name="patno2"]', chartNo)` → 填病歷號
3. `page.press('input[name="patno2"]', 'Enter')` → 觸發 AJAX 自動帶入病人資料（姓名/生日/性別）
4. 等 2 秒讓 AJAX 回傳
5. 設定 `inspectiondate`（用 JS `.value =`）、`inspectiontime`（fill）
6. `page.select_option` 選 `examroom`、`attendingdoctor1`、`attendingdoctor2`
7. 用 `page.evaluate` 設定 `pdijson` 和 `phcjson`（見下方 ID 映射）
8. 提交 ADD：`buttonName.name = "ADD"; buttonName.value = "ADD"; submit()`

### 修改 (UPT)
1. 點擊表格中的 row（JS 找 `#hes_patno` 匹配病歷號後 `row.click()`）→ 自動載入該 row 資料到表單
2. 修改需要的欄位（如 pdijson、phcjson、note）
3. 提交 UPT：`buttonName.name = "UPT"; buttonName.value = "UPT"; submit()`

### 刪除 (DEL) — 改期同步用
**關鍵**：server 靠 row 的 `<input name="chk" value="{index}">` 勾選狀態決定要刪哪筆。直接 `form.submit()` with `buttonName="DEL"` **不會刪任何東西**（因為 chk[] 空）。

正確流程：
1. `page.on("dialog", lambda d: d.accept())` — 先註冊 confirm() 自動按確定
2. JS 找到目標 row：`row.querySelector('input[name="chk"]')` → `cb.checked = true; cb.onclick()`（onclick 會呼叫 `checkedShowButton()` 自動 enable `#deleteButton`）
3. `page.click('#deleteButton')` → 觸發 `deleteMsg()` confirm() → 送出 form with `buttonName=DEL`
4. 等 networkidle + sleep 1s，再 QRY 驗證該 chart 消失

實作位置：`reschedule_webcvis.py` 的 `check_row_checkbox()` + `submit_del()`。

### pdijson / phcjson ID 映射
術前診斷和預計心導管不是純文字，需要 JSON 格式 `[{"name":"CAD","id":"PDI20090908120009"}]`。

**取得 ID 的方法**：
1. 導航到 popup 頁面：
   - 術前診斷: `/WEBCVIS/HCO/HCO1N002.do?pageid=HCO1N002&pdijson=`
   - 預計心導管: `/WEBCVIS/HCO/HCO1N004.do?pageid=HCO1N004&phcjson=`
2. 這些頁面用 dTree 渲染，格式：`d.add('PDI_ID','parent_ID',"name",...)`
3. 用 regex `d\.add\('([^']+)','([^']+)',"([^"]+)"` 解析出 id、parent、name
4. 建立 `{name: id}` 和 `{parent > child: child_id}` 映射
5. 映射結果存在 `cathlab_id_maps.json`

**常用 ID**（已驗證）：
- 術前: CAD=PDI20090908120009, AMI>NSTEMI=PDI20090908120011, EP/pAf=PDI20090908120040, EP/Sinus nodal=PDI20090908120038, PAOD=PDI20110104080726, CHF=PDI20090908120050
- 心導管: Left heart cath.=PHC20090907120001, PPM=PHC20170406095748, RF ablation=PHC20090907120009, CRT=PHC20170406100014, PTA=PHC20090907120007, Both-sided=PHC20090907120003

### 讀取現有排程
```js
document.querySelectorAll("#row tr").forEach(row => {
    let patno = row.querySelector("#hes_patno")?.value;
});
```

### 注意事項
- 每次 ADD/UPT 後頁面會 reload，需重新 set_date_and_query
- 系統會跳 "資料內容是空的" 的 Message，但操作仍會成功
- 不在 phcjson 選單的項目（如 Cardioversion）改填 `input[name="note"]` 備註欄
- 李柏增不填入主刀/第二主刀醫師欄位
- AM 時間 0600+，PM 時間 1730+，非時段 H1 1800+

**Why:** 第一次嘗試用 SaveButton 失敗（disabled），改用 AddButton+UPT 流程成功。popup ID 映射是關鍵步驟。
**How to apply:** 每次導管排程 keyin 前先 scrape popup 頁面取最新 ID 映射，再逐筆 ADD+UPT。
