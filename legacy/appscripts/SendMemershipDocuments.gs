// Scriptname: SendMembershipDocuments

// Konfigurationsvariablen
const SENDMEMBERSHIPDOCUMENTS_DOC_IDS = {
  'Aufnahmeantrag': '16JkQGU4bSTPxveTY9SGHwdFFQII8Dhgz2L159fiCWXA',
  'SEPA-Lastschriftmandat': '1-yNjyBeI5KO9Ot914b5ehUFIdzFraqILxSHEiP-a_Ys',
  'Selbstauskunft': '19PtcQJ4KayPBOpLm1VJtIOUUiFXNUSmmCfm5kzIDX_c',
  'Mitgliederausweis': '1XYV_YxGlmne9hvHHDhDGlTggx4zqI_8uQbY9SHN5Mxc'
};

const SENDMEMBERSHIPDOCUMENTS_PLACEHOLDERS_MAPPING = {
  "{{vorname}}": "Vorname",
  "{{nachname}}": "Nachname",
  "{{geburtsdatum}}": "Geburtsdatum",
  "{{strasse}}": "Straße, Hausnummer ",
  "{{postleitzahl}}": "Postleitzahl",
  "{{stadt}}": "Stadt",
  "{{telefonnummer}}": "Telefonnummer",
  "{{email}}": "E-Mail-Adresse",
  "{{aufnahmedatum}}": "Aufnahmedatum",
  "{{mitgliedsnummer}}": "Mitgliedsnummer",
  "{{kreditinstitut}}": "Kreditinstitut ",
  "{{bic}}": "BIC",
  "{{iban}}": "IBAN",
  "{{datenschutzhinweis_checkbox}}": "Datenschutzerklärung ",
  "{{keinmitglied_checkbox}}": "Mitgliedschaft anderer Anbaugemeinschaften ",
  "{{lebensjahr_checkbox}}": "Mindestalter 21 Jahre",
  "{{wohnsitz_checkbox}}": "Fester Wohnsitz in Deutschland ",
  "{{lichtbild_checkbox}}": "Aktueller Lichtbildausweis ",
  "{{beitrittsdatum}}": "Beitrittsdatum"
};

const SENDMEMBERSHIPDOCUMENTS_EMAIL_SIGNATURE = "Zusätzliche Kontaktinformationen:\nCannabis Social Club Leipzig Süd e.V.\nPostfach 35 03 04\n04165 Leipzig\ninfo@csc-leipzig.eu\n+4917643291439";
const SENDMEMBERSHIPDOCUMENTS_STAR_EMOJI = "✨";
const SENDMEMBERSHIPDOCUMENTS_CLUB_NAME = "CSC Leipzig Süd e.V.";
const SENDMEMBERSHIPDOCUMENTS_MEMBERSHIP_DOCUMENTS_EMAIL_ADDRESS = "info@csc-leipzig.eu";
const SENDMEMBERSHIPDOCUMENTS_LOGGING_ACTIVE = true;
const SENDMEMBERSHIPDOCUMENTS_SHEET_NAME = "Mitglieder";
const SENDMEMBERSHIPDOCUMENTS_DATE_FORMAT = "dd.MM.yyyy";
const SENDMEMBERSHIPDOCUMENTS_QUESTIONNAIRE_URL_FAQ = "https://www.csc-leipzig.eu/faq";
const SENDMEMBERSHIPDOCUMENTS_REGISTRATION_DEADLINE_WEEKS = 8;

// Hauptfunktion
function mainSendMembershipDocuments() {
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = spreadsheet.getSheetByName(SENDMEMBERSHIPDOCUMENTS_SHEET_NAME);

    if (!sheet) {
      sendMembershipDocumentsLog(`Tabelle '${SENDMEMBERSHIPDOCUMENTS_SHEET_NAME}' nicht gefunden.`, null, true);
      return;
    }

    const data = sheet.getDataRange().getValues();
    if (data.length < 2) {
      sendMembershipDocumentsLog(`Keine Daten in der Tabelle '${SENDMEMBERSHIPDOCUMENTS_SHEET_NAME}' gefunden.`, null, true);
      return;
    }

    const headers = data[0];
    const indexZeitstempel = headers.indexOf("Zeitstempel");
    const indexEmail = headers.indexOf("E-Mail-Adresse");

    if (indexZeitstempel === -1 || indexEmail === -1) {
      sendMembershipDocumentsLog("Notwendige Spalten 'Zeitstempel' oder 'E-Mail-Adresse' nicht gefunden.", null, true);
      return;
    }

    const currentDate = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), SENDMEMBERSHIPDOCUMENTS_DATE_FORMAT);
    sendMembershipDocumentsLog(`Aktuelles Datum: ${currentDate}`);

    for (let i = 1; i < data.length; i++) {
      try {
        const row = data[i];
        const rawTimestamp = row[indexZeitstempel];
        if (!rawTimestamp) {
          sendMembershipDocumentsLog(`Zeitstempel in Zeile ${i + 1} ist leer oder ungültig.`, null, true);
          continue;
        }
        const zeitstempel = Utilities.formatDate(new Date(rawTimestamp), Session.getScriptTimeZone(), SENDMEMBERSHIPDOCUMENTS_DATE_FORMAT);

        if (zeitstempel === currentDate) {
          const emailAddress = row[indexEmail];
          if (!emailAddress || typeof emailAddress !== "string" || emailAddress.trim() === "") {
            sendMembershipDocumentsLog(`Keine gültige E-Mail-Adresse in Zeile ${i + 1} gefunden.`, null, true);
            continue;
          }
          sendMembershipDocumentsLog(`Sende Mitgliedsdokumente an: ${emailAddress}`);
          sendMembershipDocumentsSendMembershipDocuments(emailAddress, headers, row);
        }
      } catch (error) {
        sendMembershipDocumentsLog(`Fehler beim Verarbeiten der Zeile ${i + 1}: ${error.message}`, null, true);
      }
    }
  } catch (err) {
    sendMembershipDocumentsLog('FEHLER in mainSendMembershipDocuments: ' + err.message, null, true);
    throw err;
  }
}

function sendMembershipDocumentsSendMembershipDocuments(emailAddress, headers, values) {
  try {
    let attachments = [];
    for (let docName in SENDMEMBERSHIPDOCUMENTS_DOC_IDS) {
      const docId = SENDMEMBERSHIPDOCUMENTS_DOC_IDS[docName];
      if (!docId) {
        sendMembershipDocumentsLog(`Kein Dokumenten-ID für ${docName} definiert.`, null, true);
        continue;
      }

      const originalFile = DriveApp.getFileById(docId);
      if (!originalFile) {
        sendMembershipDocumentsLog(`Originaldatei mit ID ${docId} für ${docName} nicht gefunden.`, null, true);
        continue;
      }

      const tempFile = originalFile.makeCopy(docName + '_Kopie_' + new Date().getTime());
      const tempDoc = DocumentApp.openById(tempFile.getId());
      const body = tempDoc.getBody();

      for (let placeholder in SENDMEMBERSHIPDOCUMENTS_PLACEHOLDERS_MAPPING) {
        const columnName = SENDMEMBERSHIPDOCUMENTS_PLACEHOLDERS_MAPPING[placeholder];
        const valueIndex = headers.indexOf(columnName);

        if (valueIndex === -1) {
          sendMembershipDocumentsLog(`Warnung: Spalte für Platzhalter ${placeholder} ('${columnName}') nicht gefunden.`, null, false);
          continue;
        }

        let value = values[valueIndex] || "";
        if (["Aufnahmedatum", "Geburtsdatum", "Beitrittsdatum"].includes(columnName)) {
          try {
            const date = new Date(value);
            if (!isNaN(date.getTime())) {
              value = Utilities.formatDate(date, Session.getScriptTimeZone(), SENDMEMBERSHIPDOCUMENTS_DATE_FORMAT);
            } else {
              sendMembershipDocumentsLog(`Ungültiges Datum für ${columnName} in Zeile, Wert: ${value}`, null, false);
              value = "";
            }
          } catch (e) {
            sendMembershipDocumentsLog(`Fehler beim Formatieren des Datums für ${columnName}: ${e.message}`, null, false);
            value = "";
          }
        }

        if (placeholder.endsWith("_checkbox}}")) {
          value = "[x]";
        }

        body.replaceText(placeholder, value);
      }

      tempDoc.saveAndClose();

      let pdf = tempDoc.getAs('application/pdf');
      pdf.setName(docName + ".pdf");
      attachments.push(pdf);

      // Datei in den Papierkorb verschieben
      DriveApp.getFileById(tempFile.getId()).setTrashed(true);

      sendMembershipDocumentsLog(`Dokument '${docName}' erfolgreich erstellt und temporäre Kopie gelöscht.`);
    }

    const formDataLines = headers.map((header, i) => {
      let value = values[i];
      if (["Aufnahmedatum", "Geburtsdatum", "Beitrittsdatum"].includes(header)) {
        try {
          const date = new Date(value);
          if (!isNaN(date.getTime())) {
            value = Utilities.formatDate(date, Session.getScriptTimeZone(), SENDMEMBERSHIPDOCUMENTS_DATE_FORMAT);
          }
        } catch (e) {
          // ignore formatting error here
        }
      }
      if (value !== undefined && value !== '') {
        return `${header}: ${value}`;
      }
      return null;
    }).filter(line => line !== null);

    const documentsList = Object.keys(SENDMEMBERSHIPDOCUMENTS_DOC_IDS).join("\n");

    const subject = ` ${SENDMEMBERSHIPDOCUMENTS_STAR_EMOJI} Ihre Mitgliedschaftsunterlagen im PDF-Format - ${SENDMEMBERSHIPDOCUMENTS_CLUB_NAME}`;
    const body = `Vielen Dank für Ihre Anmeldung im Verein. Ihr Aufnahmeantrag wird geprüft. Im Anhang finden Sie die benötigten Dokumente im PDF-Format.

${documentsList}

Häufig gestellte Fragen
${SENDMEMBERSHIPDOCUMENTS_QUESTIONNAIRE_URL_FAQ}

Bitte schließen Sie Ihre Registrierung innerhalb der nächsten ${SENDMEMBERSHIPDOCUMENTS_REGISTRATION_DEADLINE_WEEKS} Wochen ab. Falls Sie Fragen zur Mitgliedschaft und dem Aufnahmeprozess haben, wenden Sie sich an die folgende E-Mail Adresse:
info@csc-leipzig.eu

Formulardaten:
${formDataLines.join("\n")}

${SENDMEMBERSHIPDOCUMENTS_EMAIL_SIGNATURE}`;

    MailApp.sendEmail({
      to: emailAddress,
      subject: subject,
      body: body,
      attachments: attachments,
      replyTo: SENDMEMBERSHIPDOCUMENTS_MEMBERSHIP_DOCUMENTS_EMAIL_ADDRESS
    });

    sendMembershipDocumentsLog(`E-Mail erfolgreich an ${emailAddress} gesendet.`);
  } catch (err) {
    sendMembershipDocumentsLog(`Fehler beim Senden der E-Mail an ${emailAddress}: ${err.message}`, null, true);
  }
}

function sendMembershipDocumentsLog(message, obj, isError) {
  if (!SENDMEMBERSHIPDOCUMENTS_LOGGING_ACTIVE) return;
  const prefix = "[SENDMEMBERSHIPDOCUMENTS]";
  if (obj !== undefined && obj !== null) {
    if (isError) {
      console.error(`${prefix} ${message}`, obj);
    } else {
      console.log(`${prefix} ${message}`, obj);
    }
  } else {
    if (isError) {
      console.error(`${prefix} ${message}`);
    } else {
      console.log(`${prefix} ${message}`);
    }
  }
}
