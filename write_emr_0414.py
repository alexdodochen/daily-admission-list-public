"""Write EMR data + auto F/G to 20260414 Sheet"""
import json, os, sys, time
os.chdir(r'D:\心臟內科 總醫師\行政總醫師\每日入院名單\.claude\worktrees\determined-curie')
sys.path.insert(0, '.')

from gsheet_utils import (get_spreadsheet, get_worksheet, read_all_values,
                           write_cell, write_range, add_note, group_columns,
                           set_wrap_text, set_column_widths)

with open('_write_data_0414.json', 'r', encoding='utf-8') as f:
    write_data = json.load(f)

ws = get_worksheet('20260414')
all_data = read_all_values(ws)

out = open('_write_emr_result.txt', 'w', encoding='utf-8')

# Build chart->row mapping for doctor sub-tables
# Sub-tables start after main data (row 12 = 10 patients + 1 header + 1 gap)
chart_to_subtable_row = {}
for i, row in enumerate(all_data):
    if i < 12:
        continue
    cell0 = row[0] if row else ''
    cell1 = row[1] if len(row) > 1 else ''
    # Patient rows in sub-tables have chart number in col B
    if cell1 and len(cell1) == 8 and cell1.isdigit():
        chart_to_subtable_row[cell1] = i + 1  # 1-indexed

out.write(f'Chart to subtable row mapping: {chart_to_subtable_row}\n\n')

# Also build chart->main row mapping (for name correction)
chart_to_main_row = {}
for i, row in enumerate(all_data[1:12], 2):
    chart = row[9] if len(row) > 9 else ''
    if chart:
        chart_to_main_row[chart] = i

# Also chart->ordering row
chart_to_order_row = {}
for i, row in enumerate(all_data[1:20], 2):
    if len(row) > 18 and row[13]:  # has seq number
        chart = row[18]  # col S = 病歷號
        if chart:
            chart_to_order_row[chart] = i

no_data_patients = []

for wd in write_data:
    chart = wd['chart']
    sub_row = chart_to_subtable_row.get(chart)
    if not sub_row:
        out.write(f'SKIP {chart}: not found in sub-tables\n')
        continue

    emr_name = wd['emr_name']

    if wd['no_data']:
        # Write 無資料
        write_cell(ws, sub_row, 3, '無本院一年內主治醫師門診紀錄')
        time.sleep(0.3)
        write_cell(ws, sub_row, 8, '無資料病人')
        time.sleep(0.3)
        no_data_patients.append({'name': emr_name, 'chart': chart, 'doctor': ''})
        out.write(f'NO DATA: {emr_name} ({chart}) R{sub_row}\n')
    else:
        # Write EMR to C col, summary to D col
        emr_text = wd.get('emr', '')
        summary = wd.get('summary', '')
        write_cell(ws, sub_row, 3, emr_text)
        time.sleep(0.3)
        write_cell(ws, sub_row, 4, summary[:3000])
        time.sleep(0.3)

        # Auto-fill F/G if empty
        current_f = all_data[sub_row-1][5] if len(all_data[sub_row-1]) > 5 else ''
        current_g = all_data[sub_row-1][6] if len(all_data[sub_row-1]) > 6 else ''

        if not current_f.strip() and wd['f_diag']:
            write_cell(ws, sub_row, 6, wd['f_diag'])
            time.sleep(0.2)
        if not current_g.strip() and wd['g_cath']:
            write_cell(ws, sub_row, 7, wd['g_cath'])
            time.sleep(0.2)

        # Name correction: if EMR name differs from sheet name
        sheet_name = all_data[sub_row-1][0] if all_data[sub_row-1] else ''
        if emr_name and sheet_name and emr_name != sheet_name and '...' not in emr_name:
            out.write(f'NAME FIX: {sheet_name} -> {emr_name} ({chart})\n')
            write_cell(ws, sub_row, 1, emr_name)
            time.sleep(0.2)
            # Fix in main data
            main_row = chart_to_main_row.get(chart)
            if main_row:
                write_cell(ws, main_row, 7, emr_name)  # col G = 姓名
                time.sleep(0.2)
            # Fix in ordering
            order_row = chart_to_order_row.get(chart)
            if order_row:
                write_cell(ws, order_row, 16, emr_name)  # col P = 病人姓名
                time.sleep(0.2)

        out.write(f'OK: {emr_name} ({chart}) R{sub_row} F={wd["f_diag"]} G={wd["g_cath"]}\n')

# Also update N-V ordering with auto-detected F/G
out.write('\n=== Updating N-V ordering F/G ===\n')
for wd in write_data:
    if wd['no_data'] or (not wd['f_diag'] and not wd['g_cath']):
        continue
    chart = wd['chart']
    order_row = chart_to_order_row.get(chart)
    if order_row:
        # T col = 20 (術前診斷), U col = 21 (預計心導管)
        current_t = all_data[order_row-1][19] if len(all_data[order_row-1]) > 19 else ''
        current_u = all_data[order_row-1][20] if len(all_data[order_row-1]) > 20 else ''
        if not current_t.strip() and wd['f_diag']:
            write_cell(ws, order_row, 20, wd['f_diag'])
            time.sleep(0.2)
        if not current_u.strip() and wd['g_cath']:
            write_cell(ws, order_row, 21, wd['g_cath'])
            time.sleep(0.2)
        out.write(f'  {wd["emr_name"]} R{order_row}: T={wd["f_diag"]} U={wd["g_cath"]}\n')

# Handle 無資料病人 worksheet
if no_data_patients:
    out.write(f'\n=== Writing {len(no_data_patients)} patients to 無資料病人 sheet ===\n')
    ws_nodata = get_worksheet('無資料病人')
    if ws_nodata:
        # Find doctor from main data
        for np in no_data_patients:
            for row in all_data[1:12]:
                if len(row) > 9 and row[9] == np['chart']:
                    np['doctor'] = row[3]
                    break

        # Read existing, append
        existing = read_all_values(ws_nodata)
        next_r = len([r for r in existing if any(v.strip() for v in r)]) + 1
        for np in no_data_patients:
            write_range(ws_nodata, f'A{next_r}:E{next_r}',
                       [['2026/04/14', np['doctor'], np['name'], np['chart'], '無資料病人']])
            time.sleep(0.3)
            next_r += 1
            out.write(f'  Added {np["name"]} to 無資料病人\n')

out.close()
with open('_write_emr_result.txt', 'r', encoding='utf-8') as f:
    print(f.read())
