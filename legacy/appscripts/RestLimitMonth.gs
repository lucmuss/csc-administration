// Scriptname: RestLimitMonth

// Konfigurationsvariablen
const RESTLIMITMONTH_MONTHLY_QUOTA = 50;
const RESTLIMITMONTH_LOGGING_ACTIVE = true;
const RESTLIMITMONTH_SHEET_NAME = 'Mitglieder';
const RESTLIMITMONTH_COLUMN_NAME = 'Monatsabgabe';

// Hauptfunktion
function mainRestLimitMonth() {
  try {
    const today = new Date();
    if (today.getDate() === 1) {
      const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(RESTLIMITMONTH_SHEET_NAME);
      const monatsabgabeSpalteIndex = restLimitMonthGetColumnIndexByName(sheet, RESTLIMITMONTH_COLUMN_NAME);

      if (monatsabgabeSpalteIndex === 0) {
        throw new Error("Die erforderliche Spalte 'Monatsabgabe' fehlt.");
      }

      const numRows = sheet.getLastRow() - 1; // Da die erste Zeile die Kopfzeile ist
      if (numRows > 0) {
        const resetRange = sheet.getRange(2, monatsabgabeSpalteIndex, numRows);
        resetRange.setValue(RESTLIMITMONTH_MONTHLY_QUOTA);
      }
      restLimitMonthLog('Monatliche Monatsabgabe zurückgesetzt.', { monthlyQuota: RESTLIMITMONTH_MONTHLY_QUOTA });
    } else {
      restLimitMonthLog('Heute ist nicht der 1. Tag des Monats, kein Reset ausgeführt.');
    }
  } catch (err) {
    restLimitMonthLog('FEHLER in mainRestLimitMonth', { error: err }, true);
    throw err;
  }
}

// Hilfsfunktion, um die Spaltenindex anhand des Spaltennamens zu erhalten
function restLimitMonthGetColumnIndexByName(sheet, columnName) {
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const index = headers.indexOf(columnName);
  return index >= 0 ? index + 1 : 0; // 1-basiert oder 0 wenn nicht gefunden
}

function restLimitMonthLog(message, obj, isError) {
  if (!RESTLIMITMONTH_LOGGING_ACTIVE) return;
  if (obj !== undefined) {
    if (isError) {
      console.error(`[RESTLIMITMONTH] ${message}`, obj);
    } else {
      console.log(`[RESTLIMITMONTH] ${message}`, obj);
    }
  } else {
    if (isError) {
      console.error(`[RESTLIMITMONTH] ${message}`);
    } else {
      console.log(`[RESTLIMITMONTH] ${message}`);
    }
  }
}
