// Scriptname: NotifyOrder

// Konfigurationsvariablen
const NOTIFYORDER_DAYS_WITHOUT_ORDER = 60;
const NOTIFYORDER_LOGGING_ACTIVE = true;
const NOTIFYORDER_EMAIL_SIGNATURE = "Zusätzliche Kontaktinformationen:\n" +
    "Cannabis Social Club Leipzig Süd e.V.\n" +
    "Postfach 35 03 04\n" +
    "04165 Leipzig\n" +
    "info@csc-leipzig.eu\n" +
    "+4917643291439";
const NOTIFYORDER_STAR_EMOJI = "✨";
const NOTIFYORDER_CLUB_NAME = "CSC Leipzig Süd e.V.";
const NOTIFYORDER_ORDERS_SPREADSHEET_ID = '1foQsj_ye5QxXoZ0oE9VoxlCcdJloyTGGXTuMgDMqxvI';
const NOTIFYORDER_STOCK_INFO_UNAVAILABLE = "Sortenliste derzeit nicht verfügbar.";
const NOTIFYORDER_ORDER_FORM_URL = "https://forms.gle/6GFzHVci6CNgoefT9";
const NOTIFYORDER_FAQ_URL = "https://www.csc-leipzig.eu/faq";

// Hauptfunktion
function mainNotifyOrder() {
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();

    const sheetMembers = spreadsheet.getSheetByName('Mitglieder');
    if (!sheetMembers) throw new Error("Das 'Mitglieder' Blatt wurde nicht gefunden.");

    const ordersSpreadsheet = SpreadsheetApp.openById(NOTIFYORDER_ORDERS_SPREADSHEET_ID);
    const sheetOrders = ordersSpreadsheet.getSheetByName('Bestellungen');
    if (!sheetOrders) throw new Error("Das 'Bestellungen' Blatt wurde nicht gefunden.");

    const dataMembers = sheetMembers.getDataRange().getValues();
    const dataOrders = sheetOrders.getDataRange().getValues();
    const memberHeaders = dataMembers[0];
    const orderHeaders = dataOrders[0];

    const emailIndex = memberHeaders.indexOf("E-Mail-Adresse");
    const mitgliedsnummerIndex = memberHeaders.indexOf("Mitgliedsnummer");
    const optionalNewsletterIndex = memberHeaders.indexOf("Optionaler Newsletter ");
    const akzeptiertIndex = memberHeaders.indexOf("Akzeptiert");
    const verifiziertIndex = memberHeaders.indexOf("Verifiziert");

    const timestampOrderIndex = orderHeaders.indexOf("Zeitstempel");
    const mitgliedsnummerOrderIndex = orderHeaders.indexOf("Mitgliedsnummer");

    if ([emailIndex, mitgliedsnummerIndex, optionalNewsletterIndex, akzeptiertIndex, verifiziertIndex, timestampOrderIndex, mitgliedsnummerOrderIndex].some(i => i === -1)) {
      throw new Error("Eine oder mehrere erforderliche Spalten fehlen.");
    }

    const today = new Date();
    const daysAgoDate = new Date(today);
    daysAgoDate.setDate(today.getDate() - NOTIFYORDER_DAYS_WITHOUT_ORDER);

    const stockList = notifyOrderGetStockInfo();

    // Letzte Bestellung je Mitglied ermitteln
    const lastOrderMap = {};
    for (let i = 1; i < dataOrders.length; i++) {
      const orderRow = dataOrders[i];
      const orderDate = new Date(orderRow[timestampOrderIndex]);
      const memberNumber = orderRow[mitgliedsnummerOrderIndex];
      if (!lastOrderMap[memberNumber] || lastOrderMap[memberNumber] < orderDate) {
        lastOrderMap[memberNumber] = orderDate;
      }
    }

    // Mitglieder durchlaufen und prüfen
    for (let i = 1; i < dataMembers.length; i++) {
      const memberRow = dataMembers[i];
      const memberEmail = memberRow[emailIndex];
      const memberNumber = memberRow[mitgliedsnummerIndex];
      const optionalNewsletter = memberRow[optionalNewsletterIndex];
      const akzeptiert = memberRow[akzeptiertIndex];
      const verifiziert = memberRow[verifiziertIndex];
      const lastOrderDate = lastOrderMap[memberNumber];

      if (lastOrderDate !== undefined && lastOrderDate < daysAgoDate && optionalNewsletter === "Ja" && akzeptiert === "Ja" && verifiziert === "Ja") {
        const subject = `${NOTIFYORDER_STAR_EMOJI} Wir vermissen Ihre Vorbestellungen! - ${NOTIFYORDER_CLUB_NAME}`;
        const body = `Liebes Mitglied,

wir haben festgestellt, dass Sie in den letzten ${NOTIFYORDER_DAYS_WITHOUT_ORDER} Tagen keine Bestellung bei uns aufgegeben haben. Wir möchten Sie daran erinnern, dass wir eine große Auswahl an Sorten haben, die Sie interessieren könnten:

${stockList}

Sie können Ihre Vorbestellung über den folgenden Link abgeben: 
${NOTIFYORDER_ORDER_FORM_URL}

Häufig gestellte Fragen
${NOTIFYORDER_FAQ_URL}

Besuchen Sie unsere Webseite oder kontaktieren Sie uns für weitere Informationen.

${NOTIFYORDER_EMAIL_SIGNATURE}`;

        notifyOrderSendEmail(memberEmail, subject, body);
        notifyOrderLog(`Benachrichtigung gesendet an: ${memberEmail}`);
      }
    }
  } catch (err) {
    notifyOrderLog('FEHLER in mainNotifyOrder', {error: err}, true);
    throw err;
  }
}

function notifyOrderGetStockInfo() {
  // Hier müsste eine Implementierung analog zu anderen Skripten erfolgen
  // Zum Beispiel: Abruf von Sorten und Preisen
  // Für Isolation hier Dummy-Rückgabe:
  return NOTIFYORDER_STOCK_INFO_UNAVAILABLE;
}

function notifyOrderSendEmail(emailAddress, subject, body) {
  try {
    MailApp.sendEmail({
      to: emailAddress,
      subject: subject,
      body: body
    });
  } catch (err) {
    notifyOrderLog(`FEHLER beim Senden der Email an ${emailAddress}: ${err.message}`, null, true);
  }
}

function notifyOrderLog(message, obj, isError) {
  if (!NOTIFYORDER_LOGGING_ACTIVE) return;
  if (obj !== undefined) {
    if (isError) {
      console.error(`[NOTIFYORDER] ${message}`, obj);
    } else {
      console.log(`[NOTIFYORDER] ${message}`, obj);
    }
  } else {
    if (isError) {
      console.error(`[NOTIFYORDER] ${message}`);
    } else {
      console.log(`[NOTIFYORDER] ${message}`);
    }
  }
}
