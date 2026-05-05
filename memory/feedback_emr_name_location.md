---
name: EMR病人姓名位置
description: EMR系統中病人姓名在 span#divUserSpec 元素內，在 frame.aspx 頁面，不是在其他地方找
type: feedback
---

EMR 病人姓名在 `<span id="divUserSpec">` 內提取，不要在其他地方找。

頁面 URL 格式：`http://hisweb.hosp.ncku/Emrquery/(session)/tree/frame.aspx`

HTML 結構範例：
```html
<span id="divUserSpec">姓名 : 王樹英 , 生日 : 1932/10/20 , 性別 : 女 , 血型 : B+, 初診時間 : 1988/09/13 , 最近看診 : 2022/08/16</span>
```

提取方式：用 CSS selector `#divUserSpec` 取得文字內容，再用正則或字串分割取出「姓名 : XXX」的部分。

**Why:** 之前 EMR 提取常常找不到病人姓名，因為在錯誤的位置搜尋。

**How to apply:** EMR extraction 時，進入 frame.aspx 頁面後，直接用 `document.getElementById('divUserSpec').textContent` 或 CSS selector `#divUserSpec` 取得姓名，再 parse 出姓名欄位。
