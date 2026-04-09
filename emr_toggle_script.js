// ============================================================
// Google Sheets Apps Script：一鍵切換 EMR 列高（C、D 欄）
// ============================================================
//
// 【設定步驟】
//  1. 打開 Google Sheet → 擴充功能 → Apps Script
//  2. 把 Code.gs 內容全部刪除，貼上這段
//  3. 儲存 → 回試算表按 F5
//  4. 選單列出現「EMR 顯示」
// ============================================================

var EMR_COLUMNS = [3, 4];   // C欄=3, D欄=4（EMR, EMR摘要）
var HEADER_ROWS = 1;
var COLLAPSED_HEIGHT = 21;

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('EMR 顯示')
    .addItem('收合 EMR', 'collapseRows')
    .addItem('展開 EMR', 'expandRows')
    .addToUi();
}

function collapseRows() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var lastRow = sheet.getLastRow();
  var lastCol = sheet.getLastColumn();
  if (lastRow <= HEADER_ROWS || lastCol < 1) return;

  var dataStartRow = HEADER_ROWS + 1;
  var numRows = lastRow - HEADER_ROWS;

  // 關鍵：把「所有欄位」都設 CLIP，不只 C/D
  // 只要有任何一欄是 WRAP，Google Sheets 就會自動撐高列高
  var allDataRange = sheet.getRange(dataStartRow, 1, numRows, lastCol);
  allDataRange.setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);

  // 設定列高
  for (var r = dataStartRow; r <= lastRow; r++) {
    sheet.setRowHeight(r, COLLAPSED_HEIGHT);
  }

  SpreadsheetApp.getActiveSpreadsheet().toast('EMR 已收合', '完成', 3);
}

function expandRows() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var lastRow = sheet.getLastRow();
  var lastCol = sheet.getLastColumn();
  if (lastRow <= HEADER_ROWS || lastCol < 1) return;

  var dataStartRow = HEADER_ROWS + 1;
  var numRows = lastRow - HEADER_ROWS;

  // 把 C、D 欄改回 WRAP，讓 EMR 內容完整顯示
  EMR_COLUMNS.forEach(function(col) {
    sheet.getRange(dataStartRow, col, numRows, 1)
      .setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
  });

  // 自動調整列高（依內容）
  sheet.autoResizeRows(dataStartRow, numRows);

  SpreadsheetApp.getActiveSpreadsheet().toast('EMR 已展開', '完成', 3);
}
