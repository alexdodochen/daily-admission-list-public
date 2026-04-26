---
name: admission-cathlab-keyin
description: Use when entering catheter lab scheduling data (導管排程 key-in) into the hospital CVIS system. Triggered when user says "導管排程", "key-in導管", "排導管", or after admission ordering completes. Handles login, date setting, saving existing data, entering new patients, and verification.
---

# 導管排程 key-in（WEBCVIS）

## 何時用
入院序排定後，把該批病人推進 WEBCVIS 排程系統。每位病人的 cathlab date = 入院日 +1（週五入院 → 同日；週三入院由張獻元收 → 同日 PM；見 CLAUDE.md rule #5 例外）。

## 流程

### 1. 蒐集要 keyin 的病人

從目標日期 sheet 讀子表格（已有 EMR/F/G）或 N-V，整理成清單。每位病人需要：

| 欄位 | 來源 |
|---|---|
| `cathlab_date` | YYYY/MM/DD 格式 |
| `name` / `chart` | 子表格 A/B 欄 |
| `doctor` | 主治醫師中文名（cathlab_keyin.py 內已有 25 醫師代碼） |
| `second` | 第二醫師（無則 null） |
| `room` | H1 / H2 / C1 / C2（查 `schedule_readable.txt` 該醫師當天時段） |
| `time` | 時段醫師：上午 0600+ / 下午 1800+；非時段醫師 H1 2100+ |
| `diagnosis` | 子表格 F 欄（如 CAD / pAf / SSS） |
| `procedure` | 子表格 G 欄（如 Left heart cath. / PPM / RF ablation） |
| `note` | 可選：「本日無時段」「無資料病人」「無床改期」等 |

### 2. 寫成 JSON 檔

```bash
# cathlab_patients_20260428.json
[
  {"cathlab_date": "2026/04/28", "name": "陳爽", "chart": "04668242",
   "doctor": "黃睦翔", "second": null, "room": "C2", "time": "1801",
   "diagnosis": "CAD", "procedure": "Left heart cath.", "note": ""}
]
```

### 3. 跑通用 driver

```bash
python cathlab_keyin.py cathlab_patients_20260428.json
```

`cathlab_keyin.py` 自動：
- WEBCVIS 登入（107614 / 107614）
- 兩階段：Phase 1 ADD（依病歷號 dedupe，重複自動 SKIP）→ Phase 2 UPT（補 pdijson/phcjson，部分欄位首次 ADD 不會 stick）
- 最後驗證每個 cathlab date 的 final chart list，逐人報 OK / MISSING
- 完整 log 寫到 `_cathlab_keyin_<jsonbasename>.log`

### 4. 驗證

```bash
python verify_cathlab.py 20260427  # 驗 4/27 入院日 對應的 4/28 cathlab
```

## 重要規則

1. **PDI/PHC ID 一律從 `cathlab_id_maps.json` 載**（66 diag + 22 proc 已驗證）。`cathlab_keyin.py` 啟動時自動載；若 ID 缺失（新術式/診斷），WEBCVIS 查到後**永久寫進 cathlab_id_maps.json**，不要在 .py 內硬編（見 `feedback_cathlab_id_maps_only.md` — 我曾把 SSS/PTA ID 自編寫錯）

2. **病人已 pre-keyed → SKIP ADD + 仍跑 UPT**（per `feedback_webcvis_preserve_existing_slot.md`）。Phase 1 自動依病歷號 dedupe，Phase 2 只補 F/G

3. **跳過規則**：子表格 H 欄含「不排程」「檢查」→ 從 JSON 中排除。「無床改期」「非導管床」「HF AE」**不**跳過（見 CLAUDE.md rule #9）

4. **N-V V 欄有值 = 改期**：該病人不進該日 cathlab keyin，從 JSON 排除（見 CLAUDE.md rule #5 reschedule 部分）

5. **時段查詢權威**：`schedule_readable.txt`（cathlab 房間時段表，與抽籤表 `主治醫師抽籤表` 不同用途；見 `feedback_two_doctor_sheets.md`）

6. **只 ADD 不修不刪既有**（CLAUDE.md rule #6）

## 不要再做的事

- ❌ 每天複製 200 行 `_cathlab_keyin_MMDD.py` per-date script — 用 `cathlab_keyin.py` + JSON 取代
- ❌ 在 .py 內硬編 `DIAG_IDS = {...}` — 一律走 JSON 載入
