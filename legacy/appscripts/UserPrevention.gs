// Scriptname: UserPrevention
// ==========================

// Konfigurationsvariablen
// ==========================
var USERPREVENTION_EMAIL_SUCHT = "praevention@csc-leipzig.eu";
var USERPREVENTION_CONSUMPTION_THRESHOLD = 20; // Schwellenwert in Gramm
var USERPREVENTION_DAYS_WINDOW = 60; // Zeitfenster in Tagen
var USERPREVENTION_MEMBER_SHEET_ID = '14Bj8W64yVm6tZzrfGrhZym__kziJ_9eWw8nOB6fDGYI';
var USERPREVENTION_MEMBER_SHEET_NAME = 'Mitglieder';
var USERPREVENTION_ORDER_SHEET_NAME = 'Bestellungen';
var USERPREVENTION_LOGGING_ENABLED = true;

// E-Mail-Templates mit Platzhaltern
var USERPREVENTION_EMAIL_TEMPLATES = {
  RISK_SUMMARY: {
    subject: "Zusammenfassung der Risiko Abnehmer - {datum}",
    body: "Zusammenfassung der Risiko Abnehmer im Zeitraum {startDatum} bis {endDatum} (Schwelle: {threshold}g):\n\n{summary}\n\nDies ist eine automatisch generierte Benachrichtigung."
  }
};

// ==========================
// Hauptfunktion
// ==========================
function mainUserPrevention() {
  if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[START] mainUserPrevention gestartet");
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(USERPREVENTION_ORDER_SHEET_NAME);
    if (!sheet) {
      if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[ERROR] Das Arbeitsblatt '" + USERPREVENTION_ORDER_SHEET_NAME + "' konnte nicht gefunden werden.");
      return;
    }

    var data = sheet.getDataRange().getValues();
    if (data.length < 2) {
      if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[INFO] Keine Daten zum Überprüfen gefunden.");
      return;
    }

    var headers = data[0];
    var memberNumberIndex = headers.indexOf("Mitgliedsnummer");
    var totalAmountIndex = headers.indexOf("Gesamt Menge");
    var statusIndex = headers.indexOf("Bestellstatus");

    if (memberNumberIndex === -1 || totalAmountIndex === -1 || statusIndex === -1) {
      if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[ERROR] Die erforderlichen Spalten fehlen.");
      return;
    }

    var endDate = new Date();
    var startDate = new Date(endDate);
    startDate.setDate(endDate.getDate() - USERPREVENTION_DAYS_WINDOW);

    if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[INFO] Überprüfe Verbrauch von " + startDate.toLocaleDateString() + " bis " + endDate.toLocaleDateString());

    var consumptionByUser = {};

    for (var i = 1; i < data.length; i++) {
      var orderDate = new Date(data[i][0]);
      if (orderDate >= startDate && orderDate <= endDate && data[i][statusIndex] === "abgeschlossen") {
        var memberNumber = data[i][memberNumberIndex];
        var amount = parseFloat(data[i][totalAmountIndex]) || 0;
        if (!consumptionByUser[memberNumber]) {
          consumptionByUser[memberNumber] = 0;
        }
        consumptionByUser[memberNumber] += amount;
        if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[INFO] Bestellung: Mitglied " + memberNumber + ", Menge: " + amount + "g, Kumuliert: " + consumptionByUser[memberNumber] + "g");
      }
    }

    var summaryLines = [];
    for (var memberNumber in consumptionByUser) {
      if (consumptionByUser[memberNumber] > USERPREVENTION_CONSUMPTION_THRESHOLD) {
        var memberInfo = userPreventionGetMemberDetails(memberNumber);
        if (memberInfo) {
          summaryLines.push(
            `${memberNumber} - ${consumptionByUser[memberNumber]}g - ${memberInfo.firstName} - ${memberInfo.lastName} - ${memberInfo.phoneNumber} - ${memberInfo.email}`
          );
          if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[RISK] Risikobenutzer: " + summaryLines[summaryLines.length - 1]);
        } else {
          if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[WARN] Mitgliedsdetails nicht gefunden für: " + memberNumber);
        }
      }
    }

    // E-Mail nur senden, wenn Risikonutzer gefunden wurden
    if (summaryLines.length > 0) {
      userPreventionSendRiskSummaryEmail(summaryLines, startDate, endDate);
    } else {
      if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[INFO] Keine Risikobenutzer gefunden.");
    }
    if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[END] mainUserPrevention fertig");
  } catch (error) {
    if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[EXCEPTION] " + error.message);
  }
}

// ==========================
// Hilfsfunktionen
// ==========================
function userPreventionGetMemberDetails(memberNumber) {
  try {
    var membersSheet = SpreadsheetApp.openById(USERPREVENTION_MEMBER_SHEET_ID).getSheetByName(USERPREVENTION_MEMBER_SHEET_NAME);
    if (!membersSheet) {
      if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[ERROR] Das Arbeitsblatt '" + USERPREVENTION_MEMBER_SHEET_NAME + "' konnte nicht gefunden werden.");
      return null;
    }

    var membersData = membersSheet.getDataRange().getValues();
    var memberHeaders = membersData[0];
    var memberNumberIndex = memberHeaders.indexOf("Mitgliedsnummer");
    var firstNameIndex = memberHeaders.indexOf("Vorname");
    var lastNameIndex = memberHeaders.indexOf("Nachname");
    var phoneIndex = memberHeaders.indexOf("Telefonnummer");
    var emailIndex = memberHeaders.indexOf("E-Mail-Adresse");

    if (memberNumberIndex === -1 || firstNameIndex === -1 || lastNameIndex === -1 || phoneIndex === -1 || emailIndex === -1) {
      if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[ERROR] Fehlende Spalten im Mitgliederblatt.");
      return null;
    }

    for (var i = 1; i < membersData.length; i++) {
      if (membersData[i][memberNumberIndex] == memberNumber) {
        var memberInfo = {
          firstName: membersData[i][firstNameIndex],
          lastName: membersData[i][lastNameIndex],
          phoneNumber: membersData[i][phoneIndex],
          email: membersData[i][emailIndex]
        };
        if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[INFO] Mitgliedsdetails gefunden: " + JSON.stringify(memberInfo));
        return memberInfo;
      }
    }
    if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[INFO] Keine Mitgliedsdetails gefunden für: " + memberNumber);
    return null;
  } catch (error) {
    if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[EXCEPTION] userPreventionGetMemberDetails: " + error.message);
    return null;
  }
}

function userPreventionSendRiskSummaryEmail(summaryLines, startDate, endDate) {
  var template = USERPREVENTION_EMAIL_TEMPLATES.RISK_SUMMARY;
  var placeholders = {
    datum: endDate.toLocaleDateString(),
    startDatum: startDate.toLocaleDateString(),
    endDatum: endDate.toLocaleDateString(),
    threshold: USERPREVENTION_CONSUMPTION_THRESHOLD,
    summary: summaryLines.join("\n")
  };
  var subject = userPreventionReplacePlaceholders(template.subject, placeholders);
  var body = userPreventionReplacePlaceholders(template.body, placeholders);

  MailApp.sendEmail(USERPREVENTION_EMAIL_SUCHT, subject, body);
  if (USERPREVENTION_LOGGING_ENABLED) Logger.log("[EMAIL] E-Mail gesendet an: " + USERPREVENTION_EMAIL_SUCHT + ", Betreff: " + subject);
}

function userPreventionReplacePlaceholders(str, vars) {
  for (var key in vars) {
    str = str.replace(new RegExp("\\{" + key + "\\}", "g"), vars[key]);
  }
  return str;
}
