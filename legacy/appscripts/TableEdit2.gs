// Scriptname: TableEdit

// ==========================
// Konfigurationsvariablen
// ==========================
var TABLEEDIT_STAR_EMOJI = "✨";
var TABLEEDIT_LIGHT_GREEN_COLOR = "#90EE90";
var TABLEEDIT_LIGHT_CYAN_COLOR = "#E0FFFF";

var TABLEEDIT_EMAIL_SIGNATURE =
  "<u>Zusätzliche Kontaktinformationen:</u><br>" +
  "Cannabis Social Club Leipzig Süd e.V.<br>" +
  "Postfach 35 03 04<br>" +
  "04165 Leipzig<br>" +
  "info@csc-leipzig.eu<br>" +
  "+4917643291439<br>";

var TABLEEDIT_EMAIL_TEMPLATES = {
  FEHLER_BESTAND: {
    subject: "{star} Bestellung fehlerhaft - {club}",
    body: "Ihre Vorbestellungsanfrage konnte nicht bearbeitet werden, da folgende Sorten nicht ausreichend verfügbar sind:<br>{stockInfo}<br><br>Häufig gestellte Fragen<br><a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a><br><br>{signature}"
  },
  FEHLER_TAGESKONTINGENT: {
    subject: "{star} Bestellung fehlerhaft - {club}",
    body: "Ihre Vorbestellungsanfrage konnte nicht bearbeitet werden, da Ihr <b>tägliches Kontingent</b> überschritten wird. Ihr tägliches Kontingent beträgt: <b>{dailyQuota}g</b>.<br><br>Häufig gestellte Fragen<br><a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a><br><br>{signature}"
  },
  FEHLER_MONATSKONTINGENT: {
    subject: "{star} Bestellung fehlerhaft - {club}",
    body: "Ihre Vorbestellungsanfrage konnte nicht bearbeitet werden, da Ihr <b>monatliches Kontingent</b> überschritten wird. Ihr monatliches Kontingent beträgt: <b>{monthlyQuota}g</b>.<br><br>Häufig gestellte Fragen<br><a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a><br><br>{signature}"
  },
  ABHOLUNG_BEREIT: {
    subject: "{star} Bestellstatus: Abholung bereit - {club}",
    body: "Deine Bestellung wurde nun <b>verpackt und ist nun zur Abholung bereit</b>. Der zusätzliche Mitgliedsbeitrag zu deiner Bestellung kann Vorort mit EC oder Kreditkarte bezahlt werden. Bitte hole deine Bestellung bis <b>Ende des aktuellen Monats</b> in der Ausgabe Station ab, da die Bestellung sonst storniert wird.<br><br>Häufig gestellte Fragen<br><a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a><br><br>{signature}"
  },
  RECHNUNG: {
    subject: "{star} Ihre Rechnung zur Bestellung - {club}",
    body: "Im Anhang finden Sie Ihre Rechnung als PDF. Vielen Dank für Ihre Bestellung!<br><br>Häufig gestellte Fragen<br><a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a><br><br>{signature}"
  }
};

var TABLEEDIT_CLUB_NAME = "CSC Leipzig Süd e.V.";
var TABLEEDIT_LOGGING_ENABLED = true;
var TABLEEDIT_ORDER_SHEET_NAME = "Bestellungen";
var TABLEEDIT_MEMBER_SHEET_ID = '14Bj8W64yVm6tZzrfGrhZym__kziJ_9eWw8nOB6fDGYI';
var TABLEEDIT_MEMBER_SHEET_NAME = 'Mitglieder';
var TABLEEDIT_SORTEN_SHEET_ID = '1UhlFHxVeCPGTFkc73hyrhD4Vj22yHpGniQwsD46eZl4';
var TABLEEDIT_SORTEN_SHEET_NAME = 'Sorten';
var TABLEEDIT_RECHNUNG_TEMPLATE_DOC_ID = '12gYTGf7FQoFXOe5mhb7L3Q0RHgucrryy3fBVq5uDQTM';

// ==========================
// Hauptfunktion
// ==========================
function mainTableEdit(e) {
  Logger.clear();
  Logger.log("[START] mainTableEdit");

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(TABLEEDIT_ORDER_SHEET_NAME);
  if (!sheet) throw new Error("Das Arbeitsblatt '" + TABLEEDIT_ORDER_SHEET_NAME + "' konnte nicht gefunden werden.");

  var range = e.range;
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

  var statusColumnIndex = headers.indexOf("Bestellstatus") + 1;
  var memberNumberIndex = headers.indexOf("Mitgliedsnummer") + 1;
  var totalAmountIndex = headers.indexOf("Gesamt Menge") + 1;
  var totalValueColumnIndex = headers.indexOf("Gesamt Wert") + 1;
  var paymentColumnIndex = headers.indexOf("Zahlungsbetrag") + 1;

  if (
    statusColumnIndex < 2 ||
    memberNumberIndex < 2 ||
    totalAmountIndex < 2 ||
    totalValueColumnIndex < 2 ||
    paymentColumnIndex < 2
  ) {
    Logger.log("Fehler: Mindestens eine Spalte wurde nicht gefunden (Index zu klein). Spalten: "
      + "Bestellstatus=" + statusColumnIndex + ", Mitgliedsnummer=" + memberNumberIndex
      + ", Gesamt Menge=" + totalAmountIndex + ", Gesamt Wert=" + totalValueColumnIndex
      + ", Zahlungsbetrag=" + paymentColumnIndex
    );
    throw new Error("Die erforderlichen Spalten fehlen (Status, Mitgliedsnummer, Gesamt Menge, Gesamt Wert, Zahlungsbetrag).");
  }

  var prices = tableEditGetSortePrices();

  // Schutz: Bearbeitung bestimmter Felder verhindern
  if (
    range.getColumn() === memberNumberIndex ||
    range.getColumn() === totalAmountIndex ||
    range.getColumn() === totalValueColumnIndex ||
    range.getColumn() === paymentColumnIndex
  ) {
    var oldValue = e.oldValue;
    if (typeof oldValue !== 'undefined') {
      sheet.getRange(range.getRow(), range.getColumn()).setValue(oldValue);
    }
    Logger.log("[STOP] Geschützte Spalte bearbeitet.");
    return;
  }

  if (range.getColumn() === statusColumnIndex) {
    var newValue = range.getValue();
    var oldValue = e.oldValue;
    var row = range.getRow();
    var rowData = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];
    var memberNumber = sheet.getRange(row, memberNumberIndex).getValue();
    var totalAmount = parseFloat(sheet.getRange(row, totalAmountIndex).getValue()) || 0;
    var totalValue = parseFloat(sheet.getRange(row, totalValueColumnIndex).getValue()) || 0;
    var paymentValue = parseFloat(sheet.getRange(row, paymentColumnIndex).getValue()) || 0;
    var memberInfo = tableEditGetMemberInfo(memberNumber);

    if (!memberInfo) {
      Logger.log("[ERROR] Mitgliedsinformationen für Mitgliedsnummer " + memberNumber + " konnten nicht gefunden werden.");
      return;
    }

    if (
      (oldValue === "offen" && (newValue === "abholung" || newValue === "fehlerhaft")) ||
      (oldValue === "abholung" && (newValue === "abgeschlossen" || newValue === "fehlerhaft"))
    ) {
      if (newValue === "fehlerhaft") {
        sheet.deleteRow(row);
        return;
      }

      if (newValue === "abholung") {
        // Bestand prüfen (nur Sorten!)
        var insufficientStock = [];
        for (var i = 0; i < headers.length; i++) {
          var headerTrim = headers[i].trim();
          if (headerTrim.startsWith("Sorte:")) {
            var sortAmount = parseFloat(sheet.getRange(row, i + 1).getValue()) || 0;
            var sorteName = headerTrim;
            if (prices[sorteName] && prices[sorteName].available < sortAmount) {
              insufficientStock.push(sorteName.replace("Sorte: ", "") + " verfügbar: " + prices[sorteName].available + " g");
            }
          }
        }
        if (insufficientStock.length > 0) {
          sheet.getRange(row, statusColumnIndex).setValue("fehlerhaft");
          tableEditSendEmailWithTemplate(
            memberInfo.emailAddress,
            "FEHLER_BESTAND",
            {
              stockInfo: insufficientStock.join("<br>"),
              star: TABLEEDIT_STAR_EMOJI,
              club: TABLEEDIT_CLUB_NAME,
              signature: TABLEEDIT_EMAIL_SIGNATURE
            },
            rowData,
            headers,
            memberInfo
          );
          sheet.deleteRow(row);
          return;
        }

        // Tageskontingent prüfen (nur Sorten)
        if (memberInfo.dailyQuota - totalAmount < 0) {
          sheet.getRange(row, statusColumnIndex).setValue("fehlerhaft");
          tableEditSendEmailWithTemplate(
            memberInfo.emailAddress,
            "FEHLER_TAGESKONTINGENT",
            {
              dailyQuota: memberInfo.dailyQuota,
              star: TABLEEDIT_STAR_EMOJI,
              club: TABLEEDIT_CLUB_NAME,
              signature: TABLEEDIT_EMAIL_SIGNATURE
            },
            rowData,
            headers,
            memberInfo
          );
          sheet.deleteRow(row);
          return;
        }

        // Monatskontingent prüfen (nur Sorten)
        if (memberInfo.monthlyQuota - totalAmount < 0) {
          sheet.getRange(row, statusColumnIndex).setValue("fehlerhaft");
          tableEditSendEmailWithTemplate(
            memberInfo.emailAddress,
            "FEHLER_MONATSKONTINGENT",
            {
              monthlyQuota: memberInfo.monthlyQuota,
              star: TABLEEDIT_STAR_EMOJI,
              club: TABLEEDIT_CLUB_NAME,
              signature: TABLEEDIT_EMAIL_SIGNATURE
            },
            rowData,
            headers,
            memberInfo
          );
          sheet.deleteRow(row);
          return;
        }

        // E-Mail an den Kunden zur Abholung bereit!
        tableEditSendEmailWithTemplate(
          memberInfo.emailAddress,
          "ABHOLUNG_BEREIT",
          {
            star: TABLEEDIT_STAR_EMOJI,
            club: TABLEEDIT_CLUB_NAME,
            signature: TABLEEDIT_EMAIL_SIGNATURE
          },
          rowData,
          headers,
          memberInfo
        );
        sheet.getRange(row, 1, 1, sheet.getLastColumn()).setBackground(TABLEEDIT_LIGHT_CYAN_COLOR);

      } else if (newValue === "abgeschlossen") {
        // Update quotas, stock, and balance wie gehabt ...
        var membersSheet = SpreadsheetApp.openById(TABLEEDIT_MEMBER_SHEET_ID).getSheetByName(TABLEEDIT_MEMBER_SHEET_NAME);
        if (!membersSheet) throw new Error("Das Arbeitsblatt 'Mitglieder' konnte nicht gefunden werden.");

        var membersData = membersSheet.getDataRange().getValues();
        var memberHeaders = membersData[0];
        var monthlyQuotaIndex = memberHeaders.indexOf("Monatsabgabe");
        var dailyQuotaIndex = memberHeaders.indexOf("Tagesabgabe");
        var balanceIndex = memberHeaders.indexOf("Guthaben");

        if (monthlyQuotaIndex === -1 || dailyQuotaIndex === -1 || balanceIndex === -1) {
          throw new Error("Die erforderlichen Spalten fehlen im Mitglieder-Blatt.");
        }

        for (var i = 1; i < membersData.length; i++) {
          if (membersData[i][memberHeaders.indexOf("Mitgliedsnummer")] == memberNumber) {
            var newMonthlyQuota = membersData[i][monthlyQuotaIndex] - totalAmount;
            var newDailyQuota = membersData[i][dailyQuotaIndex] - totalAmount;
            membersSheet.getRange(i + 1, monthlyQuotaIndex + 1).setValue(newMonthlyQuota);
            membersSheet.getRange(i + 1, dailyQuotaIndex + 1).setValue(newDailyQuota);

            var currentBalance = parseFloat(membersData[i][balanceIndex]) || 0;
            var restToPay = totalValue - currentBalance;
            if (restToPay > 0) {
              membersSheet.getRange(i + 1, balanceIndex + 1).setValue(0);
              sheet.getRange(row, paymentColumnIndex).setValue(restToPay);
            } else {
              membersSheet.getRange(i + 1, balanceIndex + 1).setValue(-restToPay);
              sheet.getRange(row, paymentColumnIndex).setValue(0);
            }
            break;
          }
        }

        var sortenSheet = SpreadsheetApp.openById(TABLEEDIT_SORTEN_SHEET_ID).getSheetByName(TABLEEDIT_SORTEN_SHEET_NAME);
        if (!sortenSheet) throw new Error("Das Arbeitsblatt 'Sorten' konnte nicht gefunden werden.");
        var stockData = sortenSheet.getDataRange().getValues();
        for (var i = 1; i < stockData.length; i++) {
          var sorteName = stockData[i][0];
          var availableIndex = headers.indexOf(sorteName) + 1;
          if (availableIndex > 1) {
            var orderedAmount = parseFloat(sheet.getRange(row, availableIndex).getValue()) || 0;
            stockData[i][2] -= orderedAmount;
            sortenSheet.getRange(i + 1, 3).setValue(stockData[i][2]);
          }
        }
        sheet.getRange(row, 1, 1, sheet.getLastColumn()).setBackground(TABLEEDIT_LIGHT_GREEN_COLOR);

        // *** Rechnung als PDF verschicken ***
        tableEditSendInvoiceEmail(
          memberInfo.emailAddress,
          rowData,
          headers,
          memberInfo,
          totalValue,
          paymentValue,
          memberNumber // Mitgliedsnummer für Kontaktdaten
        );
      }
    } else {
      range.setValue(oldValue);
    }
  }

  Logger.log("[END] mainTableEdit");
}

// ==========================
// Rechnungsgenerierung & E-Mail Versand
// ==========================
function tableEditSendInvoiceEmail(emailAddress, rowData, headers, memberInfo, totalValue, paymentValue, memberNumber) {
  var berechnungsString = tableEditBuildBerechnungString(rowData, headers);
  var kontaktdatenString = tableEditBuildKontaktdatenString(memberNumber);
  var rechnungsdatenString = tableEditBuildRechnungsdatenString(rowData, headers);

  var pdf = tableEditGenerateInvoicePdf(rowData, headers, memberInfo, berechnungsString, kontaktdatenString, rechnungsdatenString);

  var template = TABLEEDIT_EMAIL_TEMPLATES.RECHNUNG;
  var placeholders = {
    club: TABLEEDIT_CLUB_NAME,
    signature: TABLEEDIT_EMAIL_SIGNATURE,
    star: TABLEEDIT_STAR_EMOJI
  };

  var subject = tableEditReplacePlaceholders(template.subject, placeholders);
  var body = tableEditReplacePlaceholders(template.body, placeholders);

  MailApp.sendEmail({
    to: emailAddress,
    subject: subject,
    htmlBody: body,
    attachments: [pdf]
  });
  Logger.log("[RECHNUNG-EMAIL] Gesendet an: " + emailAddress + ", Betreff: " + subject);
}

function tableEditBuildBerechnungString(rowData, headers) {
  var prices = tableEditGetSortePrices();
  var postens = [];
  var summe = 0;

  for (var i = 0; i < headers.length; i++) {
    var header = headers[i].trim();
    var menge = parseFloat(rowData[i]) || 0;
    if (menge > 0 && (header.startsWith("Sorte:") || header.startsWith("Steckling:"))) {
      var preisObj = prices[header] || prices[header.trim()];
      var preis = preisObj ? preisObj.price : 0;
      var einheit = header.startsWith("Sorte:") ? "g" : "Stück";
      var einheitPreis = header.startsWith("Sorte:") ? "€/g" : "€/Stück";
      var prefix = header.startsWith("Sorte:") ? "Sorte: " : "Steckling: ";
      var artikel = header.replace("Sorte: ", "").replace("Steckling: ", ""); // Entfernen der Präfixe
      var betrag = menge * preis;
      postens.push(`${prefix}${artikel}: ${menge} ${einheit} x ${preis} ${einheitPreis} = ${betrag.toFixed(2)} EUR`);
      summe += betrag;
    }
  }
  postens.push("--------------------");
  postens.push("Gesamtsumme: " + summe.toFixed(2) + " EUR");
  return postens.join("\n");
}

function tableEditBuildKontaktdatenString(memberNumber) {
  var membersSheet = SpreadsheetApp.openById(TABLEEDIT_MEMBER_SHEET_ID).getSheetByName(TABLEEDIT_MEMBER_SHEET_NAME);
  var membersData = membersSheet.getDataRange().getValues();
  var memberHeaders = membersData[0];

  var idxVorname = memberHeaders.indexOf("Vorname");
  var idxNachname = memberHeaders.indexOf("Nachname");
  var idxStrasse = memberHeaders.indexOf("Straße, Hausnummer ");
  var idxPLZ = memberHeaders.indexOf("Postleitzahl");
  var idxStadt = memberHeaders.indexOf("Stadt");
  var idxTelefon = memberHeaders.indexOf("Telefonnummer");
  var idxEmail = memberHeaders.indexOf("E-Mail-Adresse");
  var idxMitgliedsnummer = memberHeaders.indexOf("Mitgliedsnummer");

  for (var i = 1; i < membersData.length; i++) {
    if (membersData[i][idxMitgliedsnummer] == memberNumber) {
      return (
        membersData[i][idxVorname] + " " + membersData[i][idxNachname] + "\n" +
        membersData[i][idxStrasse] + "\n" +
        membersData[i][idxPLZ] + " " + membersData[i][idxStadt] + "\n" +
        "Telefonnummer: " + membersData[i][idxTelefon] + "\n" +
        "E-Mail: " + membersData[i][idxEmail] + "\n" +
        "Mitgliedsnummer: " + membersData[i][idxMitgliedsnummer]
      );
    }
  }
  return "";
}

function tableEditBuildRechnungsdatenString(rowData, headers) {
  var idxZeitstempel = headers.indexOf("Zeitstempel");
  var idxMitgliedsnummer = headers.indexOf("Mitgliedsnummer");

  var mitgliedsnummer = rowData[idxMitgliedsnummer];
  var zeitstempelStr = rowData[idxZeitstempel];
  var ts = zeitstempelStr ? new Date(zeitstempelStr) : new Date();

  // Rechnungsnummer: YYYY-MM-DD-Mitgliedsnummer
  var jahr = ts.getFullYear();
  var monat = ('0' + (ts.getMonth() + 1)).slice(-2);
  var tag = ('0' + ts.getDate()).slice(-2);
  var rechnungsnummer = jahr + "-" + monat + "-" + tag + "-" + mitgliedsnummer;

  // Rechnungs-/Leistungsdatum: aktueller Zeitpunkt (Erstellung der Rechnung)
  var now = new Date();
  var rechnungsdatum = Utilities.formatDate(now, Session.getScriptTimeZone(), "dd.MM.yyyy");
  var leistungsdatum = rechnungsdatum;

  return "Rechnung Nr.: " + rechnungsnummer + "\n" +
         "Rechnungsdatum: " + rechnungsdatum + "\n" +
         "Leistungsdatum: " + leistungsdatum;
}

function tableEditGenerateInvoicePdf(rowData, headers, memberInfo, berechnungsString, kontaktdatenString, rechnungsdatenString) {
  var docId = TABLEEDIT_RECHNUNG_TEMPLATE_DOC_ID;
  var originalFile = DriveApp.getFileById(docId);
  var tempFile = originalFile.makeCopy("Rechnung_" + new Date().getTime());
  var tempDoc = DocumentApp.openById(tempFile.getId());
  var body = tempDoc.getBody();

  body.replaceText("\\{\\{berechnung\\}\\}", berechnungsString);
  body.replaceText("\\{\\{kontaktdaten\\}\\}", kontaktdatenString);
  body.replaceText("\\{\\{rechnungsdaten\\}\\}", rechnungsdatenString);

  tempDoc.saveAndClose();
  var pdf = tempDoc.getAs('application/pdf');
  pdf.setName("Rechnung.pdf");
  DriveApp.getFileById(tempFile.getId()).setTrashed(true);

  return pdf;
}

// ==========================
// Hilfsfunktionen
// ==========================
function tableEditGetSortePrices() {
  var sortenSheet = SpreadsheetApp.openById(TABLEEDIT_SORTEN_SHEET_ID).getSheetByName(TABLEEDIT_SORTEN_SHEET_NAME);
  if (!sortenSheet) throw new Error("Das Arbeitsblatt 'Sorten' konnte nicht gefunden werden.");
  var data = sortenSheet.getDataRange().getValues();
  var prices = {};
  for (var i = 1; i < data.length; i++) {
    var sorte = data[i][0].trim();
    var price = data[i][1];
    var available = data[i][2];
    prices[sorte] = { price: price, available: available };
  }
  return prices;
}

function tableEditGetMemberInfo(memberNumber) {
  var membersSheet = SpreadsheetApp.openById(TABLEEDIT_MEMBER_SHEET_ID).getSheetByName(TABLEEDIT_MEMBER_SHEET_NAME);
  if (!membersSheet) throw new Error("Das Arbeitsblatt 'Mitglieder' konnte nicht gefunden werden.");
  var membersData = membersSheet.getDataRange().getValues();
  var memberHeaders = membersData[0];
  var memberNumberIndex = memberHeaders.indexOf("Mitgliedsnummer");
  var emailIndex = memberHeaders.indexOf("E-Mail-Adresse");
  var statusIndex = memberHeaders.indexOf("Akzeptiert");
  var verifiedIndex = memberHeaders.indexOf("Verifiziert");
  var monthlyQuotaIndex = memberHeaders.indexOf("Monatsabgabe");
  var dailyQuotaIndex = memberHeaders.indexOf("Tagesabgabe");

  if (memberNumberIndex === -1 || emailIndex === -1 || statusIndex === -1 || verifiedIndex === -1 || monthlyQuotaIndex === -1 || dailyQuotaIndex === -1) {
    throw new Error("Notwendige Spalten fehlen im Mitglieder-Blatt.");
  }

  for (var i = 1; i < membersData.length; i++) {
    if (membersData[i][memberNumberIndex] == memberNumber) {
      return {
        emailAddress: membersData[i][emailIndex] || null,
        status: membersData[i][statusIndex] || "Nein",
        verified: membersData[i][verifiedIndex] || "Nein",
        monthlyQuota: parseFloat(membersData[i][monthlyQuotaIndex]) || 0,
        dailyQuota: parseFloat(membersData[i][dailyQuotaIndex]) || 0
      };
    }
  }
  return null;
}

function tableEditSendEmailWithTemplate(emailAddress, templateKey, customVars, rowData, headers, memberInfo) {
  var template = TABLEEDIT_EMAIL_TEMPLATES[templateKey];
  if (!template) throw new Error("Unbekannter Email-Template-Key: " + templateKey);

  var placeholders = {
    club: TABLEEDIT_CLUB_NAME,
    dailyQuota: memberInfo.dailyQuota,
    monthlyQuota: memberInfo.monthlyQuota,
    signature: TABLEEDIT_EMAIL_SIGNATURE,
    star: TABLEEDIT_STAR_EMOJI
  };
  if (customVars) {
    for (var key in customVars) {
      placeholders[key] = customVars[key];
    }
  }
  
  var subject = tableEditReplacePlaceholders(template.subject, placeholders);
  var body = tableEditReplacePlaceholders(template.body, placeholders);

  MailApp.sendEmail({
    to: emailAddress,
    subject: subject,
    htmlBody: body // E-Mail im HTML-Format senden
  });
  Logger.log("[EMAIL] Gesendet an: " + emailAddress + ", Betreff: " + subject);
}

function tableEditReplacePlaceholders(str, vars) {
  for (var key in vars) {
    str = str.replace(new RegExp("\\{" + key + "\\}", "g"), vars[key]);
  }
  return str;
}
