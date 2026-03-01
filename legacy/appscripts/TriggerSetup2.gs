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
      {func: 'mainUserPrevention', eventType: 'TIME_BASED_MONTHLY_RESET'},
      {func: 'mainCleanTable', eventType: 'TIME_BASED_WEEKLY_CLEANUP'},
      {func: 'mainTableEdit', eventType: ScriptApp.EventType.ON_EDIT}
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

    // User Prevention - Monatlicher Trigger am 1. Tag um 00:01 Uhr
    ScriptApp.newTrigger('mainUserPrevention')
      .timeBased()
      .onMonthDay(1)
      .atHour(0)
      .nearMinute(1)
      .create();
    triggerSetupLog('Monatlicher User Prevention Trigger erstellt (am 1. Tag, 00:01).');

    // Clean Table - Wöchentlicher Trigger am Montag um 00:01 Uhr
    ScriptApp.newTrigger('mainCleanTable')
      .timeBased()
      .everyWeeks(1)
      .onWeekDay(ScriptApp.WeekDay.MONDAY)
      .atHour(0)
      .nearMinute(1)
      .create();
    triggerSetupLog('Wöchentlicher Clean Table Trigger erstellt (Montag, 00:01).');

    triggerSetupLog('--- [Trigger Setup erfolgreich abgeschlossen] ---');
  } catch (err) {
    triggerSetupLog('FEHLER im Trigger Setup', {error: err}, true);
    throw err;
  }
}

// Logging-Funktion für Trigger
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
