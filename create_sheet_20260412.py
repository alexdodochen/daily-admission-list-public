"""
建立 20260412 入院清單工作表
從截圖 OCR 資料寫入 Google Sheet
"""
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from gsheet_utils import (
    get_worksheet, create_worksheet, write_range, write_row,
    format_header_row, format_data_rows, add_borders,
    set_column_widths, write_doctor_table, set_wrap_text,
    batch_update_requests
)

SHEET_NAME = '20260412'

# A-L 欄標題（12 欄）
MAIN_HEADERS = [
    '實際住院日', '開刀日', '科別', '主治醫師', '主診醫師',
    '姓名', '性別', '年齡', '歲', '病歷號碼', '病床', '入院提示'
]

# 從截圖 OCR 辨識的病人資料（A-L, 12 欄）
# 病歷號碼以文字存入保留前導零
PATIENTS = [
    ['2026-04-12', '',           '心臟血管科', '詹世鴻', '4148',  '劉明坤', '男', '88', '', '00530936', '', '2'],
    ['2026-04-12', '',           '心臟血管科', '詹世鴻', '43400', '黃瑞生', '男', '65', '', '09239638', '', '1'],
    ['2026-04-12', '2026-04-13', '心臟血管科', '詹世鴻', '41400', '吳慰民', '男', '78', '', '05924616', '', '2.3'],
    ['2026-04-12', '2026-04-13', '心臟血管科', '詹世鴻', '41411', '王俊達', '男', '50', '', '08886785', '', '3'],
    ['2026-04-12', '2026-04-13', '心臟血管科', '李文煌', '4160',  '蘇錦秀', '女', '62', '', '10880119', '', '3'],
    ['2026-04-12', '2026-04-13', '心臟血管科', '黃鼎鈞', '40599', '柯景程', '男', '77', '', '04630809', '', ''],
    ['2026-04-12', '2026-04-13', '心臟血管科', '廖瑀',   '42732', '郭正生', '男', '63', '', '22534916', '', '2'],
]

# N-T 欄標題（7 欄）
ORDERING_HEADERS = ['序號', '主治醫師', '病人姓名', '備註', '術前診斷', '預計心導管', '每日續等清單']


def group_by_doctor(patients):
    """按主治醫師分組"""
    doctors = {}
    for p in patients:
        doc = p[3]  # col D = 主治醫師
        if doc not in doctors:
            doctors[doc] = []
        doctors[doc].append({
            'name': p[5],       # col F = 姓名
            'chart_no': p[9],   # col J = 病歷號碼
            'emr': '',
            'emr_summary': '',
            'order': '',
            'diagnosis': '',
            'cathlab': '',
            'note': '',
        })
    return doctors


def main():
    output = []
    output.append(f'建立工作表: {SHEET_NAME}')

    # 1. 建立工作表
    ws = create_worksheet(SHEET_NAME, rows=100, cols=20)
    output.append(f'工作表已建立')
    time.sleep(1)

    # 2. 寫入 A-L 標題列 (row 1)
    write_range(ws, 'A1:L1', [MAIN_HEADERS])
    format_header_row(ws, 1, 12)
    time.sleep(0.5)

    # 3. 寫入病人資料 (row 2+)
    num_patients = len(PATIENTS)
    end_row = num_patients + 1
    write_range(ws, f'A2:L{end_row}', PATIENTS)
    time.sleep(0.5)

    # 格式化資料列
    format_data_rows(ws, 2, end_row, 12)
    add_borders(ws, 1, 1, end_row, 12)
    time.sleep(0.5)

    # 4. 寫入 N-T 標題列 (row 1)
    write_range(ws, 'N1:T1', [ORDERING_HEADERS])
    format_header_row(ws, 1, 7, start_col=14)
    time.sleep(0.5)

    # 5. 設定欄寬
    widths = {
        1: 100,   # A: 實際住院日
        2: 100,   # B: 開刀日
        3: 90,    # C: 科別
        4: 80,    # D: 主治醫師
        5: 70,    # E: 主診醫師
        6: 70,    # F: 姓名
        7: 40,    # G: 性別
        8: 40,    # H: 年齡
        9: 30,    # I: 歲
        10: 90,   # J: 病歷號碼
        11: 50,   # K: 病床
        12: 80,   # L: 入院提示
        14: 50,   # N: 序號
        15: 80,   # O: 主治醫師
        16: 80,   # P: 病人姓名
        17: 120,  # Q: 備註
        18: 150,  # R: 術前診斷
        19: 150,  # S: 預計心導管
        20: 100,  # T: 每日續等清單
    }
    set_column_widths(ws, widths)
    time.sleep(0.5)

    # 6. 在主資料下方建立各醫師病人表格
    doctors = group_by_doctor(PATIENTS)
    next_row = end_row + 2  # 空一行

    for doc_name, pts in doctors.items():
        output.append(f'  {doc_name}: {len(pts)} 人')
        next_row = write_doctor_table(ws, next_row, doc_name, pts)
        time.sleep(0.5)

    output.append(f'\n完成! 共 {num_patients} 位病人, {len(doctors)} 位醫師')
    output.append(f'請確認病歷號碼是否正確（OCR 容易出錯）:')
    for p in PATIENTS:
        output.append(f'  {p[3]} - {p[5]}: {p[9]}')

    # Write output to file
    with open('_create_sheet_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    print('Done! See _create_sheet_result.txt')


if __name__ == '__main__':
    main()
