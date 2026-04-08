// ============================================================
// Google Sheets Apps Script：一鍵切換 EMR 列高（C、D 欄）
// ============================================================
//
// 【設定步驟】
//  1. 打開 Google Sheet
//  2. 選單 → 擴充功能 → Apps Script
//  3. 把預設的 Code.gs 內容全部刪除，貼上這段程式碼
//  4. 按 💾 儲存
//  5. 回到試算表，重新整理頁面（F5）
//  6. 選單列會多出「EMR 顯示」選單
//  7. 點選「收合」或「展開」即可切換
// ============================================================

const EMR_COLUMNS = [3, 4];   // C欄=3, D欄=4（EMR, EMR摘要）
const HEADER_ROWS = 1;

const COLLAPSED_HEIGHT = 21;
const EXPANDED_HEIGHT = 200;

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('EMR 顯示')
    .addItem('展開 EMR 列高', 'expandRows')
    .addItem('收合 EMR 列高', 'collapseRows')
    .addSeparator()
    .addItem('智慧切換', 'toggleRows')
    .addToUi();
}

function collapseRows() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var lastRow = sheet.getLastRow();
  if (lastRow <= HEADER_ROWS) return;

  var dataStartRow = HEADER_ROWS + 1;
  var numRows = lastRow - HEADER_ROWS;

  EMR_COLUMNS.forEach(function(col) {
    sheet.getRange(dataStartRow, col, numRows, 1)
      .setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);
  });

  for (var r = dataStartRow; r <= lastRow; r++) {
    sheet.setRowHeight(r, COLLAPSED_HEIGHT);
  }

  SpreadsheetApp.getActiveSpreadsheet().toast('EMR 列高已收合', '完成', 3);
}

function expandRows() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var lastRow = sheet.getLastRow();
  if (lastRow <= HEADER_ROWS) return;

  var dataStartRow = HEADER_ROWS + 1;
  var numRows = lastRow - HEADER_ROWS;

  EMR_COLUMNS.forEach(function(col) {
    sheet.getRange(dataStartRow, col, numRows, 1)
      .setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
  });

  sheet.autoResizeRows(dataStartRow, numRows);

  SpreadsheetApp.getActiveSpreadsheet().toast('EMR 列高已展開', '完成', 3);
}

function toggleRows() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var firstDataRow = HEADER_ROWS + 1;
  if (sheet.getLastRow() < firstDataRow) return;

  var currentHeight = sheet.getRowHeight(firstDataRow);
  if (currentHeight <= COLLAPSED_HEIGHT + 5) {
    expandRows();
  } else {
    collapseRows();
  }
}
