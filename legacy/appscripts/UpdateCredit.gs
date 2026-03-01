// Scriptname: UpdateCredit

// Konfigurationsvariablen
const UPDATECREDIT_GUTHABEN_MONATLICH_INCREMENT = 24; // Konfigurierbarer Wert für das monatliche Guthaben
const UPDATECREDIT_LOGGING_ACTIVE = true; // Aktivierung des Loggings
const UPDATECREDIT_SPALTE_AKZEPTIERT = "Akzeptiert"; // Spaltenname für Akzeptanz
const UPDATECREDIT_SPALTE_VERIFIZIERT = "Verifiziert"; // Spaltenname für Verifizierung
const UPDATECREDIT_SPALTE_ZAHLUNG = "Zahlung"; // Spaltenname für Zahlung
const UPDATECREDIT_SPALTE_GUTHABEN = "Guthaben"; // Spaltenname für Guthaben

// Hauptfunktion
function mainUpdateCredit() {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Mitglieder');
    
    const akzeptiertIndex = updatecreditGetColumnIndexByName(sheet, UPDATECREDIT_SPALTE_AKZEPTIERT);
    const verifiziertIndex = updatecreditGetColumnIndexByName(sheet, UPDATECREDIT_SPALTE_VERIFIZIERT);
    const zahlungIndex = updatecreditGetColumnIndexByName(sheet, UPDATECREDIT_SPALTE_ZAHLUNG);
    const guthabenIndex = updatecreditGetColumnIndexByName(sheet, UPDATECREDIT_SPALTE_GUTHABEN);
    
    if (akzeptiertIndex === 0 || verifiziertIndex === 0 || zahlungIndex === 0 || guthabenIndex === 0) {
      updatecreditLog("Die erforderlichen Spalten 'Akzeptiert', 'Verifiziert', 'Zahlung' oder 'Guthaben' fehlen.", null, true);
      return;
    }

    const numRows = sheet.getLastRow();
    if (numRows <= 1) {
      updatecreditLog("Keine Daten zum Aktualisieren vorhanden.");
      return;
    }
    const data = sheet.getRange(2, 1, numRows - 1, sheet.getLastColumn()).getValues();

    for (let i = 0; i < data.length; i++) {
      try {
        const row = data[i];
        if (row[akzeptiertIndex - 1] === "Ja" && row[verifiziertIndex - 1] === "Ja" && row[zahlungIndex - 1] === "Ja") {
          let currentGuthaben = row[guthabenIndex - 1] || 0;
          sheet.getRange(i + 2, guthabenIndex).setValue(currentGuthaben + UPDATECREDIT_GUTHABEN_MONATLICH_INCREMENT);
          updatecreditLog(`Guthaben für Mitglied in Zeile ${i + 2} erfolgreich aktualisiert.`);
        }
      } catch (error) {
        updatecreditLog(`Fehler beim Aktualisieren des Guthabens in Zeile ${i + 2}: ${error.message}`, null, true);
      }
    }
  } catch (err) {
    updatecreditLog('FEHLER in mainUpdateCredit', {error: err}, true);
    throw err;
  }
}

function mainSetGuthabenAufNull() {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Mitglieder');
    const guthabenIndex = updatecreditGetColumnIndexByName(sheet, UPDATECREDIT_SPALTE_GUTHABEN);
    
    if (guthabenIndex === 0) {
      updatecreditLog("Die erforderliche Spalte 'Guthaben' fehlt.", null, true);
      return;
    }

    const numRows = sheet.getLastRow();
    if (numRows > 1) {
      sheet.getRange(2, guthabenIndex, numRows - 1, 1).setValue(0);
      updatecreditLog(`Das Guthaben aller Mitglieder wurde erfolgreich auf 0 gesetzt.`);
    } else {
      updatecreditLog("Keine Daten zum Zurücksetzen vorhanden.");
    }
  } catch (err) {
    updatecreditLog('FEHLER in mainSetGuthabenAufNull', {error: err}, true);
    throw err;
  }
}

// Hilfsfunktionen
function updatecreditGetColumnIndexByName(sheet, columnName) {
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const index = headers.indexOf(columnName);
  return index >= 0 ? index + 1 : 0;
}

function updatecreditLog(message, obj, isError) {
  if (!UPDATECREDIT_LOGGING_ACTIVE) return;
  if (obj !== undefined) {
    if (isError) {
      console.error(`[UPDATECREDIT] ${message}`, obj);
    } else {
      console.log(`[UPDATECREDIT] ${message}`, obj);
    }
  } else {
    if (isError) {
      console.error(`[UPDATECREDIT] ${message}`);
    } else {
      console.log(`[UPDATECREDIT] ${message}`);
    }
  }
}
