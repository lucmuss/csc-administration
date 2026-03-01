// Scriptname: RestLimitDay

// Konfigurationsvariablen
const RESTLIMITDAY_DAILY_QUOTA = 25;
const RESTLIMITDAY_LOGGING_ACTIVE = true;
const RESTLIMITDAY_SHEET_NAME = 'Mitglieder';
const RESTLIMITDAY_COLUMN_NAME = 'Tagesabgabe';

// Hauptfunktion
function mainRestLimitDay() {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(RESTLIMITDAY_SHEET_NAME);
    const tagesabgabeSpalteIndex = restLimitDayGetColumnIndexByName(sheet, RESTLIMITDAY_COLUMN_NAME);

    if (tagesabgabeSpalteIndex === 0) {
      throw new Error("Die erforderliche Spalte 'Tagesabgabe' fehlt.");
    }

    const numRows = sheet.getLastRow() - 1; // Da die erste Zeile die Kopfzeile ist
    if (numRows > 0) {
      const resetRange = sheet.getRange(2, tagesabgabeSpalteIndex, numRows);
      resetRange.setValue(RESTLIMITDAY_DAILY_QUOTA);
    }
    restLimitDayLog('Tägliche Tagesabgabe zurückgesetzt.', { dailyQuota: RESTLIMITDAY_DAILY_QUOTA });
  } catch (err) {
    restLimitDayLog('FEHLER in mainRestLimitDay', { error: err }, true);
    throw err;
  }
}

// Hilfsfunktion, um die Spaltenindex anhand des Spaltennamens zu erhalten
function restLimitDayGetColumnIndexByName(sheet, columnName) {
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const index = headers.indexOf(columnName);
  return index >= 0 ? index + 1 : 0; // 1-basiert oder 0 wenn nicht gefunden
}

function restLimitDayLog(message, obj, isError) {
  if (!RESTLIMITDAY_LOGGING_ACTIVE) return;
  if (obj !== undefined) {
    if (isError) {
      console.error(`[RESTLIMITDAY] ${message}`, obj);
    } else {
      console.log(`[RESTLIMITDAY] ${message}`, obj);
    }
  } else {
    if (isError) {
      console.error(`[RESTLIMITDAY] ${message}`);
    } else {
      console.log(`[RESTLIMITDAY] ${message}`);
    }
  }
}
