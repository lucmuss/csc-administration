// Scriptname: TriggerSetup

// Konfigurationsvariablen
const TRIGGERSETUP_LOGGING_ACTIVE = true;

// Hauptfunktion zur Triggererstellung aus allen Scripten
function mainTriggerSetupCreateAllTriggers() {
  try {
    triggerSetupLog('--- [Trigger Setup gestartet] ---');

    const allTriggers = ScriptApp.getProjectTriggers();

    // Liste der Trigger-Funktionen und Event-Typen aus allen Scripten
    const triggerDefinitions = [
      {func: 'mainFormSubmit', eventType: ScriptApp.EventType.FORM_SUBMIT},
      {func: 'mainTableEdit', eventType: ScriptApp.EventType.ON_EDIT},
      {func: 'mainRestLimitDay', eventType: 'TIME_BASED_DAILY_RESET'},
      {func: 'mainRestLimitMonth', eventType: 'TIME_BASED_MONTHLY_RESET'},
      {func: 'mainUpdateCredit', eventType: 'TIME_BASED_MONTHLY_UPDATE'},
      {func: 'mainNotifyOrder', eventType: 'TIME_BASED_BIWEEKLY'},
      {func: 'mainSendLetter', eventType: 'TIME_BASED_DAILY_SENDLETTER'},
      {func: 'mainSendMembershipDocuments', eventType: 'TIME_BASED_DAILY_SENDMEMBERSHIPDOCS'},
      {func: 'mainMembershipInvitation', eventType: 'TIME_BASED_DAILY_MEMBERSHIPINVITATION'},
      {func: 'mainContactSync', eventType: 'TIME_BASED_MONTHLY_CONTACTSYNC'}  // Neu hinzugefügt
    ];

    // Lösche existierende Trigger der definierten Funktionen
    for (const trigger of allTriggers) {
      const func = trigger.getHandlerFunction();
      for (const def of triggerDefinitions) {
        if (func === def.func) {
          ScriptApp.deleteTrigger(trigger);
          triggerSetupLog(`Trigger gelöscht: ${func}`);
        }
      }
    }

    // Erstelle neue Trigger
    // Form Submit Trigger
    ScriptApp.newTrigger('mainFormSubmit')
      .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
      .onFormSubmit()
      .create();
    triggerSetupLog('FormSubmit Trigger erstellt.');

    // On Edit Trigger
    ScriptApp.newTrigger('mainTableEdit')
      .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
      .onEdit()
      .create();
    triggerSetupLog('OnEdit Trigger erstellt.');

    // RestLimitDay - Täglicher Reset Trigger auf 00:01 Uhr
    ScriptApp.newTrigger('mainRestLimitDay')
      .timeBased()
      .everyDays(1)
      .atHour(0)
      .nearMinute(1)
      .create();
    triggerSetupLog('Täglicher RestLimitDay Reset Trigger erstellt.');

    // RestLimitMonth - Monatlicher Reset Trigger am 1. des Monats 00:01 Uhr
    ScriptApp.newTrigger('mainRestLimitMonth')
      .timeBased()
      .onMonthDay(1)
      .atHour(0)
      .nearMinute(1)
      .create();
    triggerSetupLog('Monatlicher RestLimitMonth Reset Trigger erstellt.');

    // Guthaben - Monatlicher Guthaben Update Trigger am 1. des Monats 00:01 Uhr
    ScriptApp.newTrigger('mainUpdateCredit')
      .timeBased()
      .onMonthDay(1)
      .atHour(0)
      .nearMinute(1)
      .create();
    triggerSetupLog('Monatlicher Guthaben Update Trigger erstellt.');

    // ContactSync - Monatlicher Trigger am 1. des Monats 00:01 Uhr
    ScriptApp.newTrigger('mainContactSync')
      .timeBased()
      .onMonthDay(1)
      .atHour(0)
      .nearMinute(1)
      .create();
    triggerSetupLog('Monatlicher ContactSync Trigger erstellt.');

    // NotifyOrder - Biweekly Order Check Trigger montags um 11 Uhr, alle 2 Wochen
    ScriptApp.newTrigger('mainNotifyOrder')
      .timeBased()
      .everyWeeks(2)
      .onWeekDay(ScriptApp.WeekDay.MONDAY)
      .atHour(11)
      .create();
    triggerSetupLog('Biweekly Order Check Trigger erstellt.');

    // SendLetter - Täglicher Trigger um 23:59 Uhr
    ScriptApp.newTrigger('mainSendLetter')
      .timeBased()
      .everyDays(1)
      .atHour(23)
      .nearMinute(59)
      .create();
    triggerSetupLog('Täglicher SendLetter Trigger erstellt.');

    // SendMembershipDocuments - Täglicher Trigger um 23:59 Uhr
    ScriptApp.newTrigger('mainSendMembershipDocuments')
      .timeBased()
      .everyDays(1)
      .atHour(23)
      .nearMinute(59)
      .create();
    triggerSetupLog('Täglicher SendMembershipDocuments Trigger erstellt.');

    // MembershipAssemblyInvitation - Täglicher Trigger um 11 Uhr
    ScriptApp.newTrigger('mainMembershipInvitation')
      .timeBased()
      .everyDays(1)
      .atHour(11)
      .create();
    triggerSetupLog('Täglicher MembershipAssemblyInvitation Trigger erstellt.');

    triggerSetupLog('--- [Trigger Setup erfolgreich abgeschlossen] ---');
  } catch (err) {
    triggerSetupLog('FEHLER im Trigger Setup', {error: err}, true);
    throw err;
  }
}

function triggerSetupLog(message, obj, isError) {
  if (!TRIGGERSETUP_LOGGING_ACTIVE) return;
  if (obj !== undefined) {
    if (isError) {
      console.error(`[TRIGGERSETUP] ${message}`, obj);
    } else {
      console.log(`[TRIGGERSETUP] ${message}`, obj);
    }
  } else {
    if (isError) {
      console.error(`[TRIGGERSETUP] ${message}`);
    } else {
      console.log(`[TRIGGERSETUP] ${message}`);
    }
  }
}
