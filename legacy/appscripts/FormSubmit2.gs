// Scriptname: FormSubmit
// ==========================

// Konfigurationsvariablen
// ==========================
var FORMSUBMIT_CLUB_NAME = "CSC Leipzig Süd e.V.";
var FORMSUBMIT_STAR_EMOJI = "✨";
var FORMSUBMIT_DEFAULT_BACKGROUND_COLOR = "#B7CDE8";
var FORMSUBMIT_EMAIL_SIGNATURE =
  "<u>Zusätzliche Kontaktinformationen:</u><br>" +
  "Cannabis Social Club Leipzig Süd e.V.<br>" +
  "Postfach 35 03 04<br>" +
  "04165 Leipzig<br>" +
  "info@csc-leipzig.eu<br>" +
  "+4917643291439<br>";

var FORMSUBMIT_MAX_MONTHS_IN_ADVANCE = 3;
var FORMSUBMIT_DAILY_LIMIT = 25;
var FORMSUBMIT_MONTHLY_LIMIT = 50;

var FORMSUBMIT_SORTEN_SHEET_ID = '1UhlFHxVeCPGTFkc73hyrhD4Vj22yHpGniQwsD46eZl4';
var FORMSUBMIT_SORTEN_SHEET_NAME = 'Sorten';
var FORMSUBMIT_MEMBER_SHEET_ID = '14Bj8W64yVm6tZzrfGrhZym__kziJ_9eWw8nOB6fDGYI';
var FORMSUBMIT_MEMBER_SHEET_NAME = 'Mitglieder';
var FORMSUBMIT_ORDER_SHEET_NAME = 'Bestellungen';

var FORMSUBMIT_LOGGING_ENABLED = true;

// Email-Konfiguration mit Platzhaltern
var FORMSUBMIT_EMAIL_TEMPLATES = {
  ERFOLG: {
    subject: "{star} Bestellung erfolgreich aufgegeben - {club}",
    body:
      "Ihre Vorbestellungsanfrage wurde erfolgreich aufgegeben. Bitte warten Sie auf eine <b>Bestätigung per E-Mail</b>, dass die Bestellung zur Abholung bereit ist. Dieser Prozess kann mehrere Tage dauern.<br><br>" +
      "Häufig gestellte Fragen<br>" +
      "<a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a>"
  },
  FEHLER_BESTAND: {
    subject: "{star} Bestellung fehlerhaft - {club}",
    body:
      "Ihre Vorbestellungsanfrage konnte nicht bearbeitet werden, da folgende <b>Sorten nicht ausreichend verfügbar</b> sind:<br><br>{stockInfo}<br><br>" +
      "Häufig gestellte Fragen<br>" +
      "<a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a>"
  },
  FEHLER_MONAT_VERGANGEN: {
    subject: "{star} Bestellung fehlerhaft: Vergangener Ausgabe Monat - {club}",
    body:
      "Ihre Vorbestellungsanfrage konnte nicht bearbeitet werden, da der angegebene Ausgabe Monat bereits <b>in der Vergangenheit</b> liegt.<br><br>" +
      "Häufig gestellte Fragen<br>" +
      "<a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a>"
  },
  FEHLER_MONAT_ZUWEIT: {
    subject: "{star} Bestellung fehlerhaft: Zu weiter voraus geplant - {club}",
    body:
      "Ihre Vorbestellungsanfrage konnte nicht bearbeitet werden, da der angegebene Ausgabe Monat zu weit <b>in der Zukunft</b> liegt (mehr als {maxMonthsInAdvance} Monate).<br><br>" +
      "Häufig gestellte Fragen<br>" +
      "<a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a>"
  },
  FEHLER_STATUS: {
    subject: "{star} Bestellstatus: Nicht akzeptiert - {club}",
    body:
      "Die Vorbestellungsanfrage konnte leider nicht entgegen genommen werden, da ihr Mitgliedsstatus <b>noch offen</b> ist und sie <b>noch nicht verifiziert</b> wurden. Nach der Aufnahme in der Verein erhalten Sie eine E-Mail vom Vorstand. Bitte klären Sie das mit dem Vorstand ab.<br><br>" +
      "Häufig gestellte Fragen<br>" +
      "<a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a>"
  },
  FEHLER_VERIFIZIERT: {
    subject: "{star} Bestellstatus: Nicht verifiziert - {club}",
    body:
      "Die Vorbestellungsanfrage konnte leider nicht entgegen genommen werden, da ihr Mitgliedsstatus <b>noch offen</b> ist und sie <b>noch nicht verifiziert</b> wurden. Eine Mitglieder Verifizierung kann per Video Call oder Telefon Anruf erfolgen. Bitte klären Sie das mit dem Vorstand ab.<br><br>" +
      "Häufig gestellte Fragen<br>" +
      "<a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a>"
  },
  FEHLER_TAGESLIMIT: {
    subject: "{star} Fehler: Tageslimit überschritten - {club}",
    body:
      "Ihre Vorbestellungsanfrage konnte nicht bearbeitet werden, da Ihr <b>tägliches Kontingent</b> überschritten wird. Sie können maximal {dailyLimit}g am Tag beziehen.<br><br>" +
      "Häufig gestellte Fragen<br>" +
      "<a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a>"
  },
  FEHLER_MONATSLIMIT: {
    subject: "{star} Fehler: Monatslimit überschritten - {club}",
    body:
      "Ihre Vorbestellungsanfrage konnte nicht bearbeitet werden, da Ihr <b>monatliches Kontingent</b> überschritten wird. Sie können maximal {monthlyLimit}g im Monat beziehen.<br><br>" +
      "Häufig gestellte Fragen<br>" +
      "<a href='https://www.csc-leipzig.eu/faq'>https://www.csc-leipzig.eu/faq</a>"
  }
};

// ==========================
// Hauptfunktion
// ==========================
function mainFormSubmit(e) {
  if (FORMSUBMIT_LOGGING_ENABLED) Logger.log("[START] mainFormSubmit ausgelöst");

  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(FORMSUBMIT_ORDER_SHEET_NAME);
    var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

    var totalColumnIndex = formSubmitEnsureColumn(sheet, headers, "Gesamt Menge");
    var totalValueColumnIndex = formSubmitEnsureColumn(sheet, headers, "Gesamt Wert");
    var statusColumnIndex = formSubmitEnsureColumn(sheet, headers, "Bestellstatus", ['offen', 'abholung', 'abgeschlossen', 'fehlerhaft']);

    var row = sheet.getLastRow();
    var rowData = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];

    var memberNumberIndex = headers.indexOf("Mitgliedsnummer");
    var memberNumber = rowData[memberNumberIndex];
    var issueMonthIndex = headers.indexOf("Ausgabe Monat");
    var issueMonth = rowData[issueMonthIndex];

    var memberInfo = formSubmitGetMemberInfo(memberNumber);
    if (!memberInfo || !memberInfo.emailAddress) {
      if (FORMSUBMIT_LOGGING_ENABLED) Logger.log(`[FEHLER] Mitglied ${memberNumber} existiert nicht.`);
      sheet.deleteRow(row);
      return;
    }

    var prices = formSubmitGetSortePrices();
    var totalAmount = formSubmitCalculateTotalAmount(rowData, headers);
    var insufficientStock = [];

    for (var i = 0; i < headers.length; i++) {
      if (headers[i].startsWith("Sorte:") || headers[i].startsWith("Steckling:")) {
        var sortAmount = parseFloat(rowData[i]) || 0;
        if (sortAmount > 0) {
          var sorteName = headers[i];
          if (prices[sorteName]) {
            var available = prices[sorteName].available;
            if (available < sortAmount) {
              insufficientStock.push(
                sorteName +
                " verfügbar: " +
                available +
                (sorteName.startsWith("Sorte:") ? " g" : " Stück")
              );
            }
          }
        }
      }
    }

    if (insufficientStock.length > 0) {
      formSubmitSendOrderEmailWithTemplate(
        memberInfo.emailAddress,
        "FEHLER_BESTAND",
        {
          stockInfo: insufficientStock.join("<br>")
        },
        rowData, headers, memberInfo
      );
      sheet.deleteRow(row);
      return;
    }

    var currentDate = new Date();
    var currentMonth = currentDate.getMonth() + 1;
    var currentYear = currentDate.getFullYear();
    var issueMonthParts = issueMonth.split(".");
    var issueMonthValue = parseInt(issueMonthParts[0], 10);
    var issueYearValue = parseInt(issueMonthParts[1], 10);
    var currentMonthYear = currentYear * 12 + currentMonth;
    var issueMonthYear = issueYearValue * 12 + issueMonthValue;

    if (issueMonthYear < currentMonthYear) {
      formSubmitSendOrderEmailWithTemplate(memberInfo.emailAddress, "FEHLER_MONAT_VERGANGEN", {}, rowData, headers, memberInfo);
      sheet.deleteRow(row);
      return;
    }
    if (issueMonthYear > currentMonthYear + FORMSUBMIT_MAX_MONTHS_IN_ADVANCE) {
      formSubmitSendOrderEmailWithTemplate(memberInfo.emailAddress, "FEHLER_MONAT_ZUWEIT", { maxMonthsInAdvance: FORMSUBMIT_MAX_MONTHS_IN_ADVANCE }, rowData, headers, memberInfo);
      sheet.deleteRow(row);
      return;
    }

    if (memberInfo.status !== "Ja") {
      formSubmitSendOrderEmailWithTemplate(memberInfo.emailAddress, "FEHLER_STATUS", {}, rowData, headers, memberInfo);
      sheet.deleteRow(row);
      return;
    }
    if (memberInfo.verified !== "Ja") {
      formSubmitSendOrderEmailWithTemplate(memberInfo.emailAddress, "FEHLER_VERIFIZIERT", {}, rowData, headers, memberInfo);
      sheet.deleteRow(row);
      return;
    }

    if (totalAmount > FORMSUBMIT_DAILY_LIMIT) {
      formSubmitSendOrderEmailWithTemplate(memberInfo.emailAddress, "FEHLER_TAGESLIMIT", { dailyLimit: FORMSUBMIT_DAILY_LIMIT }, rowData, headers, memberInfo);
      sheet.deleteRow(row);
      return;
    }

    var totalForMonth = totalAmount;
    var allData = sheet.getDataRange().getValues();
    var statusIndex = headers.indexOf("Bestellstatus");
    for (var i = 1; i < allData.length; i++) {
      var dataRow = allData[i];
      if (dataRow[memberNumberIndex] === memberNumber &&
        dataRow[issueMonthIndex] === issueMonth &&
        dataRow[statusIndex] === "abgeschlossen") {
        totalForMonth += formSubmitCalculateTotalAmount(dataRow, headers);
      }
    }
    if (totalForMonth > FORMSUBMIT_MONTHLY_LIMIT) {
      formSubmitSendOrderEmailWithTemplate(memberInfo.emailAddress, "FEHLER_MONATSLIMIT", { monthlyLimit: FORMSUBMIT_MONTHLY_LIMIT }, rowData, headers, memberInfo);
      sheet.deleteRow(row);
      return;
    }

    var calculatedTotalValue = formSubmitCalculateTotalValue(rowData, headers, prices);

    sheet.getRange(row, totalColumnIndex + 1).setValue(totalAmount);
    sheet.getRange(row, totalValueColumnIndex + 1).setValue(calculatedTotalValue);
    sheet.getRange(row, statusColumnIndex + 1).setValue("offen");
    sheet.getRange(row, 1, 1, sheet.getLastColumn()).setBackground(FORMSUBMIT_DEFAULT_BACKGROUND_COLOR);

    formSubmitSendOrderEmailWithTemplate(memberInfo.emailAddress, "ERFOLG", {}, rowData, headers, memberInfo);

    if (FORMSUBMIT_LOGGING_ENABLED) Logger.log("[ENDE] mainFormSubmit erfolgreich");
  } catch (err) {
    if (FORMSUBMIT_LOGGING_ENABLED) Logger.log("[FEHLER] " + err.toString());
    throw err;
  }
}

// ==========================
// Hilfsfunktionen
// ==========================
function formSubmitCalculateTotalAmount(rowData, headers) {
  var totalAmount = 0;
  for (var i = 0; i < headers.length; i++) {
    var header = headers[i];
    if (header.startsWith("Sorte:")) {
      var sortAmount = parseFloat(rowData[i]) || 0;
      totalAmount += sortAmount;
    }
  }
  return totalAmount;
}

function formSubmitCalculateTotalValue(rowData, headers, sortePrices) {
  var totalValue = 0;
  for (var i = 0; i < headers.length; i++) {
    var header = headers[i];
    var sortAmount = parseFloat(rowData[i]) || 0;
    if ((header.startsWith("Sorte:") || header.startsWith("Steckling:")) && sortAmount > 0) {
      if (sortePrices[header]) {
        totalValue += sortAmount * sortePrices[header].price;
      }
    }
  }
  return totalValue;
}

function formSubmitSendOrderEmailWithTemplate(emailAddress, templateKey, customVars, rowData, headers, memberInfo) {
  var template = FORMSUBMIT_EMAIL_TEMPLATES[templateKey];
  if (!template) throw new Error("Unbekannter Email-Template-Key: " + templateKey);

  var placeholders = {
    star: FORMSUBMIT_STAR_EMOJI,
    club: FORMSUBMIT_CLUB_NAME,
    maxMonthsInAdvance: FORMSUBMIT_MAX_MONTHS_IN_ADVANCE,
    dailyLimit: FORMSUBMIT_DAILY_LIMIT,
    monthlyLimit: FORMSUBMIT_MONTHLY_LIMIT
  };
  if (customVars) {
    for (var key in customVars) {
      placeholders[key] = customVars[key];
    }
  }
  var subject = formSubmitReplacePlaceholders(template.subject, placeholders);
  var body = formSubmitReplacePlaceholders(template.body, placeholders);

  var additionalInfo = formSubmitGenerateOrderDetails(rowData, headers, memberInfo);
  var finalBody = body + "<br><br>" + additionalInfo + "<br><br>" + FORMSUBMIT_EMAIL_SIGNATURE;

  MailApp.sendEmail({
    to: emailAddress,
    subject: subject,
    htmlBody: finalBody
  });

  if (FORMSUBMIT_LOGGING_ENABLED) Logger.log(`[EMAIL] Gesendet an: ${emailAddress}, Betreff: ${subject}`);
}

function formSubmitGenerateOrderDetails(rowData, headers, memberInfo) {
  var statusIndex = headers.indexOf("Bestellstatus");
  var issueMonthIndex = headers.indexOf("Ausgabe Monat");
  var timestampIndex = headers.indexOf("Zeitstempel");
  var timestamp = rowData[timestampIndex];
  var formattedDate = Utilities.formatDate(new Date(timestamp), Session.getScriptTimeZone(), "dd.MM.yyyy HH:mm");

  var sortePrices = formSubmitGetSortePrices();

  var calculatedTotalValue = formSubmitCalculateTotalValue(rowData, headers, sortePrices);

  var orderedSortsAndAmounts = [];
  for (var i = 0; i < headers.length; i++) {
    var header = headers[i];
    var sortAmount = parseFloat(rowData[i]) || 0;
    if ((header.startsWith("Sorte:") || header.startsWith("Steckling:")) && sortAmount > 0) {
      var einheit = header.startsWith("Sorte:") ? "g" : " Stück";
      orderedSortsAndAmounts.push(`${orderedSortsAndAmounts.length + 1}. ${header}: ${sortAmount}${einheit}`);
    }
  }

  var sorteVerfuegbarkeitArr = [];
  var stecklingVerfuegbarkeitArr = [];
  Object.keys(sortePrices).forEach(function (sorte) {
    var info = sortePrices[sorte];
    var sorteName = sorte.replace("Sorte: ", ""); // Entferne "Sorte: "
    var stecklingName = sorte.replace("Steckling: ", ""); // Entferne "Steckling: "

    if (sorte.startsWith("Steckling")) {
      stecklingVerfuegbarkeitArr.push(
        `${stecklingName} - Preis: ${info.price}€/Stück - Verfügbarkeit: ${info.available} Stück`
      );
    } else {
      sorteVerfuegbarkeitArr.push(
        `${sorteName} - Preis: ${info.price}€/g - Verfügbarkeit: ${info.available}g`
      );
    }
  });

  var statusDescription = {
    "offen": "Die Bestellung wird geprüft",
    "abholung": "Die Bestellung ist zur Abholung bereit",
    "abgeschlossen": "Die Bestellung ist erfolgreich gewesen",
    "fehlerhaft": "Die Bestellung ist fehlerhaft und wird gelöscht"
  };

  var text =
    "<u>Zusätzliche Bestellinformationen:</u><br>" +
    "Mitgliedsnummer: <strong>" + rowData[headers.indexOf("Mitgliedsnummer")] + "</strong><br><br>" +
    "<u>Bestellte Sorten und Mengen:</u><br>" +
    (orderedSortsAndAmounts.length > 0 ? orderedSortsAndAmounts.join("<br>") + "<br>" : "") +
    "Gesamtwert der Bestellung: <b>" + calculatedTotalValue.toFixed(2) + " EUR</b><br>" +
    "Monatslimit: <b>" + memberInfo.monthlyQuota + "g</b><br>" +
    "Aktueller Bestellstatus: <b>" + (statusDescription[rowData[statusIndex]] || "Unbekannt") + "</b><br>" +
    "Ausgabe Monat: <b>" + rowData[issueMonthIndex] + "</b><br>" +
    "Bestelldatum: <b>" + formattedDate + "</b><br><br>" +
    (sorteVerfuegbarkeitArr.length > 0 ? "<u>Sorte Verfügbarkeit:</u><br>" + sorteVerfuegbarkeitArr.join("<br>") + "<br><br>" : "") +
    (stecklingVerfuegbarkeitArr.length > 0 ? "<u>Steckling Verfügbarkeit:</u><br>" + stecklingVerfuegbarkeitArr.join("<br>") : "");

  return text;
}

function formSubmitReplacePlaceholders(str, vars) {
  for (var key in vars) {
    str = str.replace(new RegExp("\\{" + key + "\\}", "g"), vars[key]);
  }
  return str;
}

function formSubmitEnsureColumn(sheet, headers, columnName, dropdownValues) {
  var colIndex = headers.indexOf(columnName);
  if (colIndex === -1) {
    colIndex = headers.length;
    sheet.getRange(1, colIndex + 1).setValue(columnName);
    headers.push(columnName);

    if (dropdownValues) {
      var statusRange = sheet.getRange(2, colIndex + 1, sheet.getMaxRows() - 1);
      var rule = SpreadsheetApp.newDataValidation()
        .requireValueInList(dropdownValues, true)
        .setAllowInvalid(false)
        .build();
      statusRange.setDataValidation(rule);
    }
    if (FORMSUBMIT_LOGGING_ENABLED) Logger.log(`[INFO] Spalte "${columnName}" wurde hinzugefügt.`);
  }
  return colIndex;
}

function formSubmitGetSortePrices() {
  if (FORMSUBMIT_LOGGING_ENABLED) Logger.log("[INFO] Lese Sortenpreise aus Tabelle");
  var sortenSheet = SpreadsheetApp.openById(FORMSUBMIT_SORTEN_SHEET_ID).getSheetByName(FORMSUBMIT_SORTEN_SHEET_NAME);
  if (!sortenSheet) throw new Error("Die Tabelle 'Sorten' konnte nicht gefunden werden.");
  var data = sortenSheet.getDataRange().getValues();
  var prices = {};
  for (var i = 1; i < data.length; i++) {
    var sorte = data[i][0];
    var price = data[i][1];
    var available = data[i][2];
    prices[sorte] = { price: price, available: available };
  }
  return prices;
}

function formSubmitGetMemberInfo(memberNumber) {
  if (FORMSUBMIT_LOGGING_ENABLED) Logger.log("[INFO] Hole Mitgliederinfo für Nummer: " + memberNumber);
  var membersSheet = SpreadsheetApp.openById(FORMSUBMIT_MEMBER_SHEET_ID).getSheetByName(FORMSUBMIT_MEMBER_SHEET_NAME);
  if (!membersSheet) throw new Error("Die Tabelle 'Mitglieder' konnte nicht gefunden werden.");
  var membersData = membersSheet.getDataRange().getValues();
  var memberHeaders = membersData[0];
  var memberNumberIndex = memberHeaders.indexOf("Mitgliedsnummer");
  var emailIndex = memberHeaders.indexOf("E-Mail-Adresse");
  var statusIndex = memberHeaders.indexOf("Akzeptiert");
  var verifiedIndex = memberHeaders.indexOf("Verifiziert");
  var monthlyQuotaIndex = memberHeaders.indexOf("Monatsabgabe");
  var dailyQuotaIndex = memberHeaders.indexOf("Tagesabgabe");
  if (memberNumberIndex === -1 || emailIndex === -1 || statusIndex === -1 || verifiedIndex === -1 || monthlyQuotaIndex === -1 || dailyQuotaIndex === -1) {
    throw new Error("Notwendige Spalten fehlen in der Mitglieder-Tabelle.");
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
