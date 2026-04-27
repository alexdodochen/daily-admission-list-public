---
name: 張獻元 週二入院 cathlab 規則（先 3 人 Tue PM，其餘 Wed AM；王/張 borrow → 全 Wed）
description: 張獻元週二 admission 的 cathlab 自動分配：H 含張倉惟/王思翰 → 全部 N+1 週三；無王/張 → 前 3 個 (E 排序) Tue PM 同日，第 4+ 個 Wed AM。週三 admission 維持同日 PM。
type: feedback
---

**規則（2026-04-27 update，覆蓋之前『改手動』版本）：**

張獻元的病人，**週二入院**時，cathlab 分配如下：

1. **H 註記含「張倉惟」或「王思翰」** → 全部排到**週三 (N+1) 張獻元時段**（W3 C2，AM 0600+ 或 PM 1800+ 依人數累計）
2. **H 註記不含張倉惟/王思翰** → 依 sub-table E 欄順序：
   - 前 3 個 → 同日週二 PM 張獻元時段（W2 PM H2，1800+1801+1802）
   - 第 4 個以上 → 隔日週三 AM 張獻元時段（W3 AM C2，0600+0601...）

張獻元**週三入院**規則維持原樣：同日做（W3 AM C2 / PM C2，依時段表）。

**Why:**
- 週二 PM H2 是張獻元自己的同日時段，但每天只有 3 個 1 小時 slot，多了塞不下 → 第 4+ 個自然 overflow 到 N+1 W3 AM
- 王思翰/張倉惟沒獨立時段，是「借」張獻元的時段，臨床上習慣全排 W3（隔日做），不混進 W2 PM
- 之前 (4/27 早上) 暫時改「全部手動」是因為自動分配規則沒講清楚，使用者重新明訂規則後恢復自動

**How to apply（cathlab JSON 建立時）：**

```python
def split_zhang_tue_admit(patients_sorted_by_E):
    """patients_sorted_by_E: list of dicts with at least 'name', 'H', etc.
    Returns (tue_pm, wed_am, wed_pm) — wed_pm 通常為 [] 除非 wed_am 也滿了。
    """
    borrowed = [p for p in patients_sorted_by_E
                if '張倉惟' in p['H'] or '王思翰' in p['H']]
    own = [p for p in patients_sorted_by_E
           if '張倉惟' not in p['H'] and '王思翰' not in p['H']]
    tue_pm = own[:3]
    wed_am = own[3:] + borrowed  # 借時段者跟自己 4+ 排同日(週三)
    wed_pm = []  # 暫不溢出 PM；若 wed_am > 4-5 人再考慮
    return tue_pm, wed_am, wed_pm
```

時段：
- W2 PM H2: room=`H2`, time=`1800+i`（i = 0,1,2）, doctor=張獻元, second=null
- W3 AM C2: room=`C2`, time=`0600+i`（從 borrowed 那一邊也接著編）, doctor=張獻元, second=患者 H 的王/張那一個
- W3 PM C2: 通常空，除非當天人爆量

**已知實例：**
- 2026-04-28 (Tue) 張獻元 8 位：
  - W/王思翰 borrow: 林志哲, 張連財, 潘韋儒 (3 人, 王思翰)
  - W/張倉惟 borrow: 林機明, 方文忠 (2 人)
  - 自己病人: 陳麗花, 王得福, 陳中坤 (3 人, 剛好 Tue PM 全收)
  - **預期排法**：Tue PM = 陳麗花/王得福/陳中坤，Wed AM = 林機明/方文忠/林志哲/張連財/潘韋儒
  - 實際 4/27 keyin 還沒套這版規則，所有 8 位都到 Wed。使用者選 (b) 接受現狀，下次 (4/29 之後) 用此規則
