// Scriptname: TableEdit

// Konfigurationsvariablen
const TABLEEDIT_BACKGROUND_COLOR_BOTH_YES = "#90EE90";
const TABLEEDIT_BACKGROUND_COLOR_ONE_YES = "#E0FFFF";
const TABLEEDIT_BACKGROUND_COLOR_NONE_YES = "#E0FFFF";
const TABLEEDIT_PREIS_EURO_WAEHRUNG = "€";
const TABLEEDIT_PREIS_EURO_GEWESE = "g";
const TABLEEDIT_PREIS_EURO_STUECK = "Stück";
const TABLEEDIT_LOGGING_ACTIVE = true;
const TABLEEDIT_EMAIL_SIGNATURE = "Zusätzliche Kontaktinformationen:\n" +
    "Cannabis Social Club Leipzig Süd e.V.\n" +
    "Postfach 35 03 04\n" +
    "04165 Leipzig\n" +
    "info@csc-leipzig.eu\n" +
    "+4917643291439";

// onEdit Event-Funktion
function mainTableEdit(e) {
  tableEditLog('Das Skript wurde gestartet.');
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Mitglieder');
    if (!sheet) {
      tableEditLog('WARNUNG: Blatt "Mitglieder" nicht gefunden.');
      return;
    }
    const range = e.range;

    const akzeptiertSpalteIndex = tableEditGetColumnIndexByName(sheet, "Akzeptiert");
    const verifiziertSpalteIndex = tableEditGetColumnIndexByName(sheet, "Verifiziert");
    const mitgliedsnummerSpalteIndex = tableEditGetColumnIndexByName(sheet, "Mitgliedsnummer");
    const monatsabgabeSpalteIndex = tableEditGetColumnIndexByName(sheet, "Monatsabgabe");
    const tagesabgabeSpalteIndex = tableEditGetColumnIndexByName(sheet, "Tagesabgabe");
    const guthabenSpalteIndex = tableEditGetColumnIndexByName(sheet, "Guthaben");
    const beitrittsdatumSpalteIndex = tableEditGetColumnIndexByName(sheet, "Beitrittsdatum");
    const aufnahmedatumSpalteIndex = tableEditGetColumnIndexByName(sheet, "Aufnahmedatum");
    const emailSpalteIndex = tableEditGetColumnIndexByName(sheet, "E-Mail-Adresse");

    const row = range.getRow();

    // Prüfen, ob die editierte Spalte die "Akzeptiert" Spalte betrifft
    if (range.getColumn() === akzeptiertSpalteIndex) {
      const oldValue = e.oldValue;
      const newValue = range.getValue();

      // Überprüfen, ob die Änderung von "Nein" auf "Ja" erfolgt ist
      if (oldValue === "Nein" && newValue === "Ja") {
        // Holen Sie sich das Aufnahmedatum
        const aufnahmedatumValue = sheet.getRange(row, aufnahmedatumSpalteIndex).getValue();
        const aufnahmedatum = new Date(aufnahmedatumValue);

        // Setzen des Beitrittsdatums auf den ersten Tag des Monats im Aufnahmedatum
        const ersterTagDesFolgendenMonats = new Date(aufnahmedatum.getFullYear(), aufnahmedatum.getMonth() + 1, 1);
        sheet.getRange(row, beitrittsdatumSpalteIndex).setValue(ersterTagDesFolgendenMonats);
      }
    }

    // Prüfen, ob die editierte Spalte die "Verifiziert" Spalte betrifft
    if (range.getColumn() === verifiziertSpalteIndex) {
      const oldValue = e.oldValue;
      const newValue = range.getValue();
      const akzeptiertValue = sheet.getRange(row, akzeptiertSpalteIndex).getValue();

      // Überprüfen, ob die Änderung von "Nein" auf "Ja" erfolgt ist
      if (oldValue === "Nein" && newValue === "Ja") {
        if (akzeptiertValue !== "Ja") {
          // Rückgängig machen der Änderung, wenn "Akzeptiert" nicht "Ja" ist
          sheet.getRange(row, verifiziertSpalteIndex).setValue(oldValue);
          return;
        }

        // Sperre die Zelle, damit der Wert nicht geändert werden kann
        sheet.getRange(row, verifiziertSpalteIndex).setNote("Dieser Wert kann nicht mehr geändert werden.");
        range.setDataValidation(null); // Entferne die Datenvalidierung, um weitere Änderungen zu verhindern
      } else if (oldValue === "Ja" && newValue === "Nein") {
        // Setze die Änderung zurück, falls der Versuch unternommen wird, von "Ja" auf "Nein" zu ändern
        sheet.getRange(row, verifiziertSpalteIndex).setValue(oldValue);
      }
    }

    // Prüfen, ob die editierte Spalte die "Akzeptiert" oder "Verifiziert" Spalte betrifft
    if (range.getColumn() === akzeptiertSpalteIndex || range.getColumn() === verifiziertSpalteIndex) {
      const akzeptiertValue = sheet.getRange(row, akzeptiertSpalteIndex).getValue();
      const verifiziertValue = sheet.getRange(row, verifiziertSpalteIndex).getValue();

      let backgroundColor;
      if (akzeptiertValue === "Ja" && verifiziertValue === "Ja") {
        backgroundColor = TABLEEDIT_BACKGROUND_COLOR_BOTH_YES;  // Beide "Ja"
      } else if (akzeptiertValue === "Ja" || verifiziertValue === "Ja") {
        backgroundColor = TABLEEDIT_BACKGROUND_COLOR_ONE_YES;  // Eines davon "Ja"
      } else {
        backgroundColor = TABLEEDIT_BACKGROUND_COLOR_NONE_YES;  // Keine von beiden "Ja", Standardfarbe (weiß)
      }
      
      // Setze die Hintergrundfarbe für die gesamte Zeile
      sheet.getRange(row, 1, 1, sheet.getLastColumn()).setBackground(backgroundColor);

      // E-Mail versenden, wenn Bedingungen erfüllt sind
      const emailAddress = sheet.getRange(row, emailSpalteIndex).getValue();
      const mitgliedsnummer = sheet.getRange(row, mitgliedsnummerSpalteIndex).getValue();
      const beitrittsdatum = sheet.getRange(row, beitrittsdatumSpalteIndex).getDisplayValue();

      if (akzeptiertValue === "Ja" && verifiziertValue === "Ja") {
        const stockList = tableEditGetStockInfo();

        const subject = "Ihr Mitgliedsantrag wurde vollständig akzeptiert und verifiziert";
        const body = `Herzlichen Glückwunsch! Ihr Mitgliedsantrag wurde vom Vorstand sowohl akzeptiert als auch verifiziert. Sie sind nun ein vollwertiges Mitglied. Weitere Informationen zum Aufnahme und Bestell-Prozess erhalten Sie in den FAQs auf unserer Webseite. Bitte lesen Sie diese durch.
        
Mitgliedsnummer: ${mitgliedsnummer}
Beitrittsdatum: ${beitrittsdatum}

Falls Sie Fragen zur Mitgliedschaft und dem Aufnahmeprozess haben, wenden Sie sich an die folgende E-Mail Adresse:
info@csc-leipzig.eu. 
Aktuelle Verfügbarkeiten an Sorten:

${stockList}

Sie können Ihre Vorbestellung über den folgenden Link abgeben.
https://forms.gle/6GFzHVci6CNgoefT9

Häufig gestellte Fragen
https://www.csc-leipzig.eu/faq

Treten Sie unserer internen Telegram Gruppe bei: 
https://t.me/+aatnXfbp7wJlZDEy

Besuchen Sie unsere Webseite oder kontaktieren Sie uns für weitere Informationen.`;

        tableEditSendEmail(emailAddress, subject, body, TABLEEDIT_EMAIL_SIGNATURE);

      } else if (akzeptiertValue === "Ja") {
        const subject = "Ihr Mitgliedsantrag wurde akzeptiert";
        const body = `Ihr Mitgliedsantrag wurde manuell vom Vorstand akzeptiert. Bitte beachten Sie, dass eine zusätzliche Verifizierung erforderlich ist. Schicken Sie uns die unterschriebenen Mitgliedsunterlagen per E-Mail oder als Brief zu. Weitere Informationen zum Aufnahme-Prozess erhalten Sie in den FAQs auf unserer Webseite. Bitte lesen Sie diese durch.
        
Mitgliedsnummer: ${mitgliedsnummer}
Beitrittsdatum: ${beitrittsdatum}

Häufig gestellte Fragen
https://www.csc-leipzig.eu/faq

Falls Sie Fragen zur Mitgliedschaft und dem Aufnahmeprozess haben, wenden Sie sich an die folgende E-Mail Adresse:
info@csc-leipzig.eu`;

        tableEditSendEmail(emailAddress, subject, body, TABLEEDIT_EMAIL_SIGNATURE);

      } else if (verifiziertValue === "Ja") {
        const subject = "Ihr Mitgliedsantrag wurde verifiziert";
        const body = `Ihr Mitgliedsantrag wurde manuell vom Vorstand verifiziert. Sie können nun alle Vereinsvorteile nutzen und Cannabis online vorbestellen. Weitere Informationen zum Bestell-Prozess erhalten Sie in den FAQs auf unserer Webseite. Bitte lesen Sie diese durch.
        
Mitgliedsnummer: ${mitgliedsnummer}
Beitrittsdatum: ${beitrittsdatum}

Häufig gestellte Fragen
https://www.csc-leipzig.eu/faq

Falls Sie Fragen zur Mitgliedschaft und dem Aufnahmeprozess haben, wenden Sie sich an die folgende E-Mail Adresse:
info@csc-leipzig.eu`;

        tableEditSendEmail(emailAddress, subject, body, TABLEEDIT_EMAIL_SIGNATURE);
      }
    }

    // Rücksetzen des alten Werts bei Änderungen in den nicht veränderbaren Spalten
    if (range.getColumn() === mitgliedsnummerSpalteIndex ||
        range.getColumn() === monatsabgabeSpalteIndex || 
        range.getColumn() === tagesabgabeSpalteIndex ||
        range.getColumn() === guthabenSpalteIndex) {
      // Setze den alten Wert zurück als Ganzzahl
      const oldValue = parseInt(e.oldValue, 10);
      if (!isNaN(oldValue)) {
        sheet.getRange(range.getRow(), range.getColumn()).setValue(oldValue);
      }
    }
  } catch (err) {
    tableEditLog('FEHLER im Skript tableEditOnEditMitglieder', {error: err});
    throw err;
  }
}

function tableEditGetSortePrices() {
  try {
    var sortenSheet = SpreadsheetApp.openById('1UhlFHxVeCPGTFkc73hyrhD4Vj22yHpGniQwsD46eZl4').getSheetByName('Sorten');
    if (!sortenSheet) {
      throw new Error("The 'Sorten' sheet could not be found.");
    }
    var data = sortenSheet.getDataRange().getValues();

    var prices = {};
    for (var i = 1; i < data.length; i++) {
      var sorte = data[i][0];
      var price = data[i][1];
      var available = data[i][2];
      prices[sorte] = { price: price, available: available };
    }
    return prices;
  } catch (err) {
    tableEditLog('FEHLER in tableEditGetSortePrices', {error: err});
    throw err;
  }
}

function tableEditGetStockInfo() {
  try {
    const sortePrices = tableEditGetSortePrices();
    const allStockInfo = Object.keys(sortePrices).map(sorte => {
      const info = sortePrices[sorte];
      const einheit = sorte.includes("Steckling") ? TABLEEDIT_PREIS_EURO_STUECK : TABLEEDIT_PREIS_EURO_GEWESE;
      return `${sorte} - Preis: ${info.price}${TABLEEDIT_PREIS_EURO_WAEHRUNG}/${einheit} - Verfügbarkeit: ${info.available} ${einheit}`;
    });

    return allStockInfo.join("\n");
  } catch (err) {
    tableEditLog('FEHLER in tableEditGetStockInfo', {error: err});
    return "";
  }
}

function tableEditSendEmail(emailAddress, subject, body, emailSignature) {
  try {
    const fullBody = `${body}\n\n${emailSignature}`;
    MailApp.sendEmail({
      to: emailAddress,
      subject: subject,
      body: fullBody
    });
    tableEditLog('Email gesendet.', {to: emailAddress, subject: subject});
  } catch (err) {
    tableEditLog('FEHLER beim Senden der Email', {error: err});
  }
}

function tableEditLog(message, obj) {
  if (!TABLEEDIT_LOGGING_ACTIVE) return;
  if (obj !== undefined) {
    console.log(`[TABLEEDIT] ${message}`, obj);
  } else {
    console.log(`[TABLEEDIT] ${message}`);
  }
}

function tableEditGetColumnIndexByName(sheet, columnName) {
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  return headers.indexOf(columnName) + 1;
}
