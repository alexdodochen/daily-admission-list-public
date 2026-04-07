"""
生成 20260408 / 20260409 住院序列 (N-T columns)
讀取 Google Sheet 醫師病人表格的 F/G/H 欄，
依據已有的 round-robin 醫師順序 + E 欄手動排序，
寫入正確的 N-T 欄位：序號|主治醫師|病人姓名|備註|術前診斷|預計心導管|每日續等清單
"""
import sys, time, json
sys.path.insert(0, '.')
from gsheet_utils import (get_spreadsheet, get_worksheet, read_all_values,
                           write_range, clear_range, format_header_row,
                           format_data_rows, add_borders, batch_update_requests)

# 正確的 N-T 欄位標題 (col N=14 to T=20)
ORDERING_HEADERS = ['序號', '主治醫師', '病人姓名', '備註', '術前診斷', '預計心導管', '每日續等清單']

def extract_doctor_tables(all_data):
    """從工作表資料中提取各醫師病人表格，回傳 {醫師: [患者dict]}"""
    doctors = {}
    current_doc = None
    header_row_seen = False

    for i, row in enumerate(all_data):
        cell0 = row[0] if row else ''
        # 醫師標題行: "柯呈諭（2人）"
        if cell0 and ('人）' in cell0 or '人)' in cell0):
            # Extract doctor name
            for sep in ['（', '(']:
                if sep in cell0:
                    current_doc = cell0.split(sep)[0].strip()
                    break
            doctors[current_doc] = []
            header_row_seen = False
            continue

        # 子表頭行
        if current_doc and cell0 == '姓名':
            header_row_seen = True
            continue

        # 病人資料行
        if current_doc and header_row_seen and cell0 and cell0 != '姓名':
            name = row[0] if len(row) > 0 else ''
            chart = row[1] if len(row) > 1 else ''
            emr_summary = row[3] if len(row) > 3 else ''
            e_order = row[4] if len(row) > 4 else ''
            f_diag = row[5] if len(row) > 5 else ''
            g_cath = row[6] if len(row) > 6 else ''
            h_note = row[7] if len(row) > 7 else ''

            doctors[current_doc].append({
                'name': name,
                'chart': chart,
                'e_order': e_order.strip() if e_order else '',
                'diagnosis': f_diag.strip() if f_diag else '',
                'cathlab': g_cath.strip() if g_cath else '',
                'note': h_note.strip() if h_note else '',
            })
            continue

        # 空行 = 結束當前醫師
        if current_doc and not cell0:
            current_doc = None
            header_row_seen = False

    return doctors


def extract_roundrobin_order(all_data):
    """從 N-O 欄 (col 14-15, 0-indexed 13-14) 提取已有的 round-robin 醫師順序"""
    doctors_order = []
    seen_docs = set()
    for row in all_data[1:]:  # skip header
        if len(row) > 14 and row[13]:  # col N has sequence number
            doc = row[14] if len(row) > 14 else ''  # col O
            if doc and doc not in seen_docs:
                doctors_order.append(doc)
                seen_docs.add(doc)
        else:
            break
    return doctors_order


def get_patient_notes_from_main(all_data):
    """從 A-L 主資料取得入院提示中的文字註記，回傳 {病歷號: 註記}"""
    notes = {}
    for row in all_data[1:]:
        if not row[0]:
            break
        chart = row[9] if len(row) > 9 else ''  # col J = 病歷號碼
        hint = row[11] if len(row) > 11 else ''  # col L = 入院提示
        if chart and hint:
            # 提取有意義的文字（去掉純數字的床位資訊）
            import re
            # 去掉開頭的數字.數字格式 (床位)
            text_part = re.sub(r'^[\d.]+\s*', '', hint).strip()
            # 去掉 003 等代碼
            text_part = re.sub(r'^0+\d+\s*', '', text_part).strip()
            if text_part:
                notes[chart] = text_part
    return notes


def sort_patients_by_e(patients):
    """依 E 欄排序病人：有 E 的按數字排，沒 E 的保持原順序填補空位"""
    if not patients:
        return patients

    # 分離有E和無E的病人
    with_e = [(p, int(p['e_order'])) for p in patients if p['e_order'].isdigit()]
    without_e = [p for p in patients if not p['e_order'].isdigit()]

    if not with_e:
        return patients  # 全部沒有 E → 保持原順序

    # 按 E 排序
    with_e.sort(key=lambda x: x[1])

    # 建立結果列表：E 值決定位置，無 E 的填補空位
    max_pos = max(e for _, e in with_e)
    total = max(max_pos, len(patients))
    result = [None] * total

    # 放入有 E 的
    for p, e in with_e:
        result[e - 1] = p  # E=1 → index 0

    # 填入無 E 的
    wi = 0
    for i in range(total):
        if result[i] is None and wi < len(without_e):
            result[i] = without_e[wi]
            wi += 1

    # 移除 None（理論上不該有）
    return [p for p in result if p is not None]


def generate_ordering(doctor_order, doctor_tables, patient_notes):
    """
    依 round-robin 順序生成入院序列
    Round-robin: A1→B1→C1→A2→B2→C2→...
    """
    # 準備各醫師排好序的病人佇列
    queues = {}
    for doc in doctor_order:
        if doc in doctor_tables:
            queues[doc] = sort_patients_by_e(doctor_tables[doc])
        else:
            queues[doc] = []

    # 各醫師目前分配到第幾個病人
    indices = {doc: 0 for doc in doctor_order}

    ordering = []
    seq = 1

    while True:
        assigned_this_round = False
        for doc in doctor_order:
            idx = indices[doc]
            if idx < len(queues[doc]):
                patient = queues[doc][idx]
                indices[doc] = idx + 1
                assigned_this_round = True

                # 備註：優先用 H 欄，補充入院提示
                note = patient['note']
                chart_note = patient_notes.get(patient['chart'], '')
                if chart_note and chart_note not in (note or ''):
                    if note:
                        note = f"{note}; {chart_note}"
                    else:
                        note = chart_note

                ordering.append([
                    str(seq),           # N: 序號
                    doc,                # O: 主治醫師
                    patient['name'],    # P: 病人姓名
                    note,               # Q: 備註
                    patient['diagnosis'],  # R: 術前診斷
                    patient['cathlab'],    # S: 預計心導管
                    '',                 # T: 每日續等清單
                ])
                seq += 1

        if not assigned_this_round:
            break

    return ordering


def write_ordering_to_sheet(ws, ordering, all_data):
    """寫入 N-T 欄位 (columns 14-20)"""
    # 1. 先修正標題列 (row 1, N-T)
    header_range = 'N1:T1'
    write_range(ws, header_range, [ORDERING_HEADERS])
    time.sleep(0.5)

    # 2. 清除舊的 N-T 資料 (row 2 onwards, enough rows)
    clear_range(ws, 'N2:T50')
    time.sleep(0.5)

    # 3. 寫入新的排序資料
    if ordering:
        end_row = len(ordering) + 1
        data_range = f'N2:T{end_row}'
        write_range(ws, data_range, ordering)
        time.sleep(0.5)

    # 4. 格式化
    format_header_row(ws, 1, 7, start_col=14)  # N-T header
    time.sleep(0.3)
    if ordering:
        add_borders(ws, 1, 14, len(ordering) + 1, 20)
    time.sleep(0.3)

    return len(ordering)


def process_sheet(sheet_name):
    """處理單一工作表"""
    ws = get_worksheet(sheet_name)
    if not ws:
        raise ValueError(f"找不到工作表: {sheet_name}")

    all_data = read_all_values(ws)

    # 提取資料
    doctor_order = extract_roundrobin_order(all_data)
    doctor_tables = extract_doctor_tables(all_data)
    patient_notes = get_patient_notes_from_main(all_data)

    result = {
        'doctor_order': doctor_order,
        'doctor_tables': {d: [(p['name'], p['e_order'], p['diagnosis'], p['cathlab'], p['note'])
                              for p in pts]
                          for d, pts in doctor_tables.items()},
        'patient_notes': patient_notes,
    }

    # 生成排序
    ordering = generate_ordering(doctor_order, doctor_tables, patient_notes)

    result['ordering'] = ordering

    # 寫入工作表
    count = write_ordering_to_sheet(ws, ordering, all_data)
    result['count'] = count

    return result


def main():
    output = []
    for sheet_name in ['20260408', '20260409']:
        output.append(f'\n{"="*50}')
        output.append(f'  Processing {sheet_name}')
        output.append(f'{"="*50}')

        try:
            result = process_sheet(sheet_name)

            output.append(f'\nRound-robin order: {" > ".join(result["doctor_order"])}')
            output.append(f'\nDoctor tables:')
            for doc, pts in result['doctor_tables'].items():
                output.append(f'  {doc} ({len(pts)} patients):')
                for name, e, diag, cath, note in pts:
                    e_str = f' E={e}' if e else ''
                    output.append(f'    {name}{e_str} | {diag} | {cath} | {note}')

            output.append(f'\nGenerated ordering ({result["count"]} entries):')
            output.append(f'  {"Seq":<4} {"Doctor":<8} {"Patient":<12} {"Note":<20} {"Diagnosis":<30} {"Cathlab"}')
            output.append(f'  {"---":<4} {"------":<8} {"-------":<12} {"----":<20} {"---------":<30} {"-------"}')
            for row in result['ordering']:
                output.append(f'  {row[0]:<4} {row[1]:<8} {row[2]:<12} {row[3]:<20} {row[4]:<30} {row[5]}')

            output.append(f'\nDone! Wrote {result["count"]} entries to {sheet_name} N-T columns.')

        except Exception as e:
            output.append(f'ERROR: {e}')
            import traceback
            output.append(traceback.format_exc())

    # Write output to file (cp950 terminal can't handle all chars)
    with open('_ordering_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))


if __name__ == '__main__':
    main()
