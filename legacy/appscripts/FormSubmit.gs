// Scriptname: FormSubmit

// Konfigurationsvariablen
const FORMSUBMIT_DEFAULT_GUTHABEN = 0;
const FORMSUBMIT_MONTHLY_FEE = 50;
const FORMSUBMIT_DAILY_FEE = 25;
const FORMSUBMIT_MINIMUM_AGE = 21;
const FORMSUBMIT_DEFAULT_BACKGROUND_COLOR = "#B7CDE8";
const FORMSUBMIT_MEMBERSHIP_DOCUMENTS_EMAIL_ADDRESS = "info@csc-leipzig.eu";
const FORMSUBMIT_DUPLICATE_CHECK_COLUMNS = ["E-Mail-Adresse"];
const FORMSUBMIT_STAR_EMOJI = "✨";
const FORMSUBMIT_CLUB_NAME = "CSC Leipzig Süd e.V.";
const FORMSUBMIT_EMAIL_SIGNATURE = "Zusätzliche Kontaktinformationen:\n" +
    "Cannabis Social Club Leipzig Süd e.V.\n" +
    "Postfach 35 03 04\n" +
    "04165 Leipzig\n" +
    "info@csc-leipzig.eu\n" +
    "+4917643291439";
// Logging
const FORMSUBMIT_LOGGING_ACTIVE = true; // Logging aktivieren/deaktivieren

// Hauptfunktion
function mainFormSubmit(e) {
  try {
    formSubmitLog('--- [Skript gestartet: mainFormSubmit] ---');

    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Mitglieder');
    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    
    const values = e.values;
    const row = e.range.getRow();

    formSubmitLog('Formular-Eingabe erhalten.', {headers, values, row});

    formSubmitLog('Überprüfe Duplikate...');
    const data = sheet.getDataRange().getValues();
    let duplicateField = null;

    for (let i = 1; i < row - 1; i++) {
      for (const columnName of FORMSUBMIT_DUPLICATE_CHECK_COLUMNS) {
        const columnIndex = formSubmitGetColumnIndexByName(sheet, columnName);
        if (data[i][columnIndex - 1] === values[columnIndex - 1]) {
          duplicateField = columnName;
          break;
        }
      }
      if (duplicateField) break;
    }

    if (duplicateField) {
      sheet.deleteRow(row);
      formSubmitSendEmail(
        values[formSubmitGetColumnIndexByName(sheet, "E-Mail-Adresse") - 1],
        "Registrierung fehlgeschlagen",
        `Die ${duplicateField} ist bereits vorhanden.`,
        FORMSUBMIT_EMAIL_SIGNATURE
      );
      formSubmitLog('Duplikat gefunden, Zeile gelöscht und Benachrichtigung gesendet.', {duplicateField});
      return;
    }

    // Altersprüfung
    const birthdate = new Date(values[formSubmitGetColumnIndexByName(sheet, "Geburtsdatum") - 1]);
    const age = formSubmitCalculateAge(birthdate);

    formSubmitLog('Alter des Mitglieds berechnet.', {birthdate, age});
    if (age < FORMSUBMIT_MINIMUM_AGE) {
      sheet.deleteRow(row);
      formSubmitSendEmail(
        values[formSubmitGetColumnIndexByName(sheet, "E-Mail-Adresse") - 1],
        "Mitgliedschaft abgelehnt",
        `Erfüllen nicht die Altersanforderung von ${FORMSUBMIT_MINIMUM_AGE} Jahren.`,
        FORMSUBMIT_EMAIL_SIGNATURE
      );
      formSubmitLog('Mindestalter nicht erreicht. Zeile gelöscht, Ablehnungs-Email gesendet.', {age});
      return;
    }

    // Aufnahmedatum & Beitrittsdatum
    const aufnahmedatum = new Date(values[formSubmitGetColumnIndexByName(sheet, "Aufnahmedatum") - 1]);
    // Mitgliedsnummer berechnen
    let mitgliedsnummerSpalte = formSubmitGetColumnIndexByName(sheet, "Mitgliedsnummer");
    if (!mitgliedsnummerSpalte) {
      mitgliedsnummerSpalte = sheet.getLastColumn() + 1;
      sheet.getRange(1, mitgliedsnummerSpalte).setValue("Mitgliedsnummer");
    }
    const membershipNumbers = data.slice(1, row - 1)
      .map(row => parseInt(row[mitgliedsnummerSpalte - 1], 10))
      .filter(num => !isNaN(num));
    const maxNumber = membershipNumbers.length > 0 ? Math.max(...membershipNumbers) : 99999;
    const newMitgliedsnummer = maxNumber + 1;
    sheet.getRange(row, mitgliedsnummerSpalte).setValue(newMitgliedsnummer.toString());
    formSubmitLog('Mitgliedsnummer vergeben.', {newMitgliedsnummer});

    // Beitrittsdatum setzen
    let beitrittsdatumSpalte = formSubmitGetColumnIndexByName(sheet, "Beitrittsdatum");
    if (!beitrittsdatumSpalte) {
      beitrittsdatumSpalte = sheet.getLastColumn() + 1;
      sheet.getRange(1, beitrittsdatumSpalte).setValue("Beitrittsdatum");
    }
    const beitrittsdatum = new Date(aufnahmedatum.getFullYear(), aufnahmedatum.getMonth() + 1, 1);
    sheet.getRange(row, beitrittsdatumSpalte).setValue(beitrittsdatum);
    formSubmitLog('Beitrittsdatum gesetzt.', {beitrittsdatum});

    // Guthaben
    let guthabenSpalte = formSubmitGetColumnIndexByName(sheet, "Guthaben");
    if (!guthabenSpalte) {
      guthabenSpalte = sheet.getLastColumn() + 1;
      sheet.getRange(1, guthabenSpalte).setValue("Guthaben");
    }
    sheet.getRange(row, guthabenSpalte).setValue(FORMSUBMIT_DEFAULT_GUTHABEN);

    // Akzeptiert 
    let akzeptiertSpalte = formSubmitGetColumnIndexByName(sheet, "Akzeptiert");
    if (!akzeptiertSpalte) {
      akzeptiertSpalte = sheet.getLastColumn() + 1;
      sheet.getRange(1, akzeptiertSpalte).setValue("Akzeptiert");
      const rangeForValidation = sheet.getRange(2, akzeptiertSpalte, sheet.getMaxRows() - 1);
      const rule = SpreadsheetApp.newDataValidation()
        .requireValueInList(['Nein', 'Ja'], true)
        .setAllowInvalid(false)
        .build();
      rangeForValidation.setDataValidation(rule);
    }
    sheet.getRange(row, akzeptiertSpalte).setValue("Nein");

    // Verifiziert
    let verifiziertSpalte = formSubmitGetColumnIndexByName(sheet, "Verifiziert");
    if (!verifiziertSpalte) {
      verifiziertSpalte = sheet.getLastColumn() + 1;
      sheet.getRange(1, verifiziertSpalte).setValue("Verifiziert");
      const verifiziertRangeForValidation = sheet.getRange(2, verifiziertSpalte, sheet.getMaxRows() - 1);
      const verifiziertRule = SpreadsheetApp.newDataValidation()
        .requireValueInList(['Nein', 'Ja'], true)
        .setAllowInvalid(false)
        .build();
      verifiziertRangeForValidation.setDataValidation(verifiziertRule);
    }
    sheet.getRange(row, verifiziertSpalte).setValue("Nein");
    
    // Zahlung
    let zahlungSpalte = formSubmitGetColumnIndexByName(sheet, "Zahlung");
    if (!zahlungSpalte) {
      zahlungSpalte = sheet.getLastColumn() + 1;
      sheet.getRange(1, zahlungSpalte).setValue("Zahlung");
      const zahlungRangeForValidation = sheet.getRange(2, zahlungSpalte, sheet.getMaxRows() - 1);
      const zahlungRule = SpreadsheetApp.newDataValidation()
        .requireValueInList(['Nein', 'Ja'], true)
        .setAllowInvalid(false)
        .build();
      zahlungRangeForValidation.setDataValidation(zahlungRule);
    }
    sheet.getRange(row, zahlungSpalte).setValue("Nein");

    // Monatsabgabe
    let monatsabgabeSpalte = formSubmitGetColumnIndexByName(sheet, "Monatsabgabe");
    if (!monatsabgabeSpalte) {
      monatsabgabeSpalte = sheet.getLastColumn() + 1;
      sheet.getRange(1, monatsabgabeSpalte).setValue("Monatsabgabe");
    }
    sheet.getRange(row, monatsabgabeSpalte).setValue(FORMSUBMIT_MONTHLY_FEE);

    // Tagesabgabe
    let tagesabgabeSpalte = formSubmitGetColumnIndexByName(sheet, "Tagesabgabe");
    if (!tagesabgabeSpalte) {
      tagesabgabeSpalte = sheet.getLastColumn() + 1;
      sheet.getRange(1, tagesabgabeSpalte).setValue("Tagesabgabe");
    }
    sheet.getRange(row, tagesabgabeSpalte).setValue(FORMSUBMIT_DAILY_FEE);

    // Telefonnummer (+ durch 00 ersetzen UND als String abspeichern, mit Apostroph)
    let telefonnummerSpalte = formSubmitGetColumnIndexByName(sheet, "Telefonnummer");
    if (telefonnummerSpalte) {
      let rawPhone = values[telefonnummerSpalte - 1];
      let normalizedPhone = formSubmitNormalizePhoneNumber(rawPhone);
      // Speichere als String (mit führendem Apostroph)
      sheet.getRange(row, telefonnummerSpalte).setValue("'" + normalizedPhone);
      formSubmitLog('Telefonnummer normalisiert und als String gespeichert.', {rawPhone, normalizedPhone});
    } else {
      formSubmitLog('WARNUNG: Telefonnummer Spalte nicht gefunden!');
    }

    // Zeile farblich hervorheben
    sheet.getRange(row, 1, 1, sheet.getLastColumn()).setBackground(FORMSUBMIT_DEFAULT_BACKGROUND_COLOR);
    formSubmitLog('Zeile eingefärbt.');

    formSubmitLog('--- [Skript erfolgreich abgeschlossen] ---');
  } catch (err) {
    formSubmitLog('FEHLER im Skript mainFormSubmit', {error: err});
    throw err; // Für Apps Script Dashboard & Debugging
  }
}

// Hilfsfunktionen

function formSubmitSendEmail(emailAddress, subject, body, emailSignature) {
  const modifiedSubject = `${FORMSUBMIT_STAR_EMOJI} ${subject} - ${FORMSUBMIT_CLUB_NAME}`;
  const fullBody = `${body}\n\n${emailSignature}`;
  MailApp.sendEmail({
    to: emailAddress,
    subject: modifiedSubject,
    body: fullBody,
    replyTo: FORMSUBMIT_MEMBERSHIP_DOCUMENTS_EMAIL_ADDRESS
  });
  formSubmitLog('Email gesendet.', {to: emailAddress, subject: modifiedSubject});
}

function formSubmitCalculateAge(birthdate) {
  const today = new Date();
  let age = today.getFullYear() - birthdate.getFullYear();
  const monthDifference = today.getMonth() - birthdate.getMonth();
  if (monthDifference < 0 || (monthDifference === 0 && today.getDate() < birthdate.getDate())) {
    age--;
  }
  return age;
}

function formSubmitLog(message, obj) {
  if (!FORMSUBMIT_LOGGING_ACTIVE) return;
  if (obj !== undefined) {
    console.log(`[FORMSUBMIT] ${message}`, obj);
  } else {
    console.log(`[FORMSUBMIT] ${message}`);
  }
}

function formSubmitGetColumnIndexByName(sheet, columnName) {
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  return headers.indexOf(columnName) + 1;
}

function formSubmitNormalizePhoneNumber(phone) {
  // Entfernt Whitespaces und ersetzt führendes + durch 00, auch bei "+49..." zu "0049..."
  let trimmed = (phone || '').trim();
  // Nur am Anfang ersetzen, falls das + wirklich am Anfang steht
  if (trimmed.startsWith('+')) {
    return trimmed.replace(/^\+/, '00');
  }
  return trimmed;
}
