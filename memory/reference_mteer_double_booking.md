---
name: MTEER 案在 WEBCVIS 出現 2 筆是正常的
description: M-TEER 一定要配 TEE 影像引導，所以同一病人同一時段會有 Hybrid 房間（介入主案）+ xa-TEE 房間（影像配套案）兩筆 booking
type: reference
originSessionId: 5aa8a056-a465-471f-90a8-3b6720110bf5
---
# MTEER WEBCVIS 雙 booking pattern

M-TEER（mitral transcatheter edge-to-edge repair, 二尖瓣經導管邊對邊修復）必須在 TEE 即時影像引導下執行。WEBCVIS 上會看到同一病人同一時段（通常）兩筆排程：

| 房間 | 角色 | VS 欄位 | Note |
|------|------|---------|------|
| `xa-Hybrid2`（或其他 Hybrid 房間）| 介入主案 | 主治（如 黃睦翔）+ 副手（如 葉建寬）| `MTEER 全麻 ICU` |
| `xa-TEE` | TEE 影像配套 | TEE 醫師（如 陳則瑋）+ 主治（如 黃睦翔）| `MTEER` |

**驗證範例（2026-05-05 劉廖寶蓮 18750900）**：
- xa-Hybrid2 1330：VS:黃睦翔 VS:葉建寬，note `MTEER 全麻 ICU`
- xa-TEE 1330：VS:陳則瑋 VS:黃睦翔，note `MTEER`

**判斷重複是否合法**：
- 兩筆 chart 相同、時間相同、note 都含 MTEER、其中一筆在 xa-TEE → 配套案，正常
- 兩筆 chart 相同、time 不同、note 不含 MTEER → 可能真的是 duplicate，要查

**verify_cathlab.py 注意**：
- 該 script 預設 N+1 cathlab 日，MTEER 病人通常排在隔週（如 5/3 入院 → 5/5 MTEER 不是 5/4）
- script 不知道 MTEER 例外，會回 NG（false positive）
- 看到「N+1 找不到」的 MR/MTEER 病人時，手動查 N+2 / 後續日期 WEBCVIS
