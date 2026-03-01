// Scriptname: MembershipInvitation.gs

// =========================
// Zentrale Konfigurationsvariablen
// =========================

const MEMBERSHIPINVITATION_ASSEMBLY_DATES = [
  '01.01',
  '01.04',
  '01.07',
  '01.10'
];

const MEMBERSHIPINVITATION_DAYS_BEFORE = 6;
const MEMBERSHIPINVITATION_EMAIL_SENDER = "info@csc-leipzig.eu";
const MEMBERSHIPINVITATION_LOGGING_ENABLED = true;
const MEMBERSHIPINVITATION_MEMBERSHIP_DOCUMENTS_EMAIL_ADDRESS = "vorstand@csc-leipzig.eu";

const MEMBERSHIPINVITATION_EMAIL_SIGNATURE = 
  "<u>Zusätzliche Kontaktinformationen:</u><br>" +
  "Cannabis Social Club Leipzig Süd e.V.<br>" +
  "Postfach 35 03 04<br>" +
  "04165 Leipzig<br>" +
  "info@csc-leipzig.eu<br>" +
  "+4917643291439";

const MEMBERSHIPINVITATION_CLUB_NAME = "CSC Leipzig Süd e.V.";
const MEMBERSHIPINVITATION_STAR_EMOJI = "✨";
const MEMBERSHIPINVITATION_SHEET_NAME = "Mitglieder";
const MEMBERSHIPINVITATION_HEADER_ACCEPTED = "Akzeptiert";
const MEMBERSHIPINVITATION_HEADER_EMAIL = "E-Mail-Adresse";
const MEMBERSHIPINVITATION_CALENDAR_ID = "098daead4e5fe87610ab8d84f9f03731b50ab24e5e434286c58b41bbd5019abb@group.calendar.google.com";

const MEMBERSHIPINVITATION_START_HOUR = 19;
const MEMBERSHIPINVITATION_START_MINUTE = 0;
const MEMBERSHIPINVITATION_END_HOUR = 21;
const MEMBERSHIPINVITATION_END_MINUTE = 0;

const MEMBERSHIPINVITATION_EVENT_DESCRIPTION =
  "Aktuelle Informationen über den Beitritt zur Mitgliedsversammlung erhaltet ihr in der E-Mail Adresse.<br><br>Join with Google Meet: <br><br>Learn more about Meet at: https://support.google.com/a/users/answer/9282720";

const MEMBERSHIPINVITATION_EVENT_SUMMARY_TEMPLATE = "Mitgliederversammlung #{{meetingNumber}} - " + MEMBERSHIPINVITATION_CLUB_NAME;

const MEMBERSHIPINVITATION_FILTER_EMAIL = ""; // z.B. "" für alle

const MEMBERSHIPINVITATION_EMAIL_SUBJECT_TEMPLATE = "{{STAR_EMOJI}} Mitgliederversammlung am {{MEETING_DATE}} – {{CLUB_NAME}}";

const MEMBERSHIPINVITATION_EMAIL_BODY_TEMPLATE = `
<p>Sehr geehrtes Mitglied,</p>

<p>wir laden Sie hiermit herzlich zu unserer nächsten ordentlichen Mitgliederversammlung ein. Bitte beachten Sie, dass die Versammlung am <strong>{{MEETING_DATE}} um ${MEMBERSHIPINVITATION_START_HOUR} Uhr</strong> stattfindet. Die Mitgliederversammlung findet in <strong>deutscher Sprache</strong> statt. Hier ist der Link zur Teilnahme:<br>
<a href="{{MEET_LINK}}">{{MEET_LINK}}</a></p>

<p>Damit die Mitgliedsversammlung reibungslos verläuft, achte bitte auf folgende Punkte. Mache dir bitte vorher Gedanken welche Punkte du einbringen möchtest. Teste vor dem Video Gespräch dein Mikrofon und deine Webcam.</p>

<p>Zu Beginn der Mitgliedsversammlung werden die Teilnehmenden dazu aufgefordert ihre Ausweis-Dokumente in die Kamera zu halten damit wir abgleichen können, ob eine Mitgliedschaft vorliegt. In der Mitgliedsversammlung dürfen nur Mitglieder abstimmen, die vollständig in den Verein aufgenommen wurden.</p>

<p>Die <strong>Tagesordnungs-Punkte</strong>, die in der Mitgliedsversammlung besprochen werden, müssen <strong>spätestens 1 Woche vor</strong> dem Stattfinden der Veranstaltung beim Vorstand eingereicht werden. Verwende dazu die folgende E-Mail Adresse: <a href="mailto:vorstand@csc-leipzig.eu">vorstand@csc-leipzig.eu</a></p>

<p>Die Protokolle der letzten Mitgliedsversammlungen findest du in unserem Google Drive Ordner. Hier ist der Link zu den Protokollen:<br>
<a href="https://drive.google.com/drive/folders/1kSJdYzuNEHvyZTPgV6MMs7AKHSeMBZXg?usp=sharing">Protokolle im Google Drive</a></p>

<p>Falls du Fragen hast zum Ablauf, kannst du an den Vorstand einfach eine E-Mail schicken.</p>

<p>Wir freuen uns auf Ihre Teilnahme!<br>Die Vorstände</p>

<p>${MEMBERSHIPINVITATION_EMAIL_SIGNATURE}</p>
`;

// =========================
// Hauptfunktion
// =========================

function mainMembershipInvitation() {
  try {
    membershipInvitationLog("Skript gestartet");
    const today = new Date();
    const currentYear = today.getFullYear();
    const upcomingDates = membershipInvitationGetUpcomingAssemblyDates(currentYear, today);

    upcomingDates.forEach((date, index) => {
      const daysUntilAssembly = Math.floor((date - today) / (1000 * 60 * 60 * 24));
      membershipInvitationLog(`Prüfe Versammlung am ${date.toDateString()} (${daysUntilAssembly} Tage entfernt).`);
      if (daysUntilAssembly === MEMBERSHIPINVITATION_DAYS_BEFORE) {
        membershipInvitationLog(`Einladung wird an Mitglieder für die Versammlung am ${date.toDateString()} gesendet.`);

        const meetingNumber = index + 1;
        const calendarEvent = membershipInvitationCreateCalendarEvent(date, meetingNumber);
        if (!calendarEvent) {
          throw new Error("Kalenderereignis konnte nicht erstellt werden.");
        }

        const meetLink = calendarEvent.conferenceData && calendarEvent.conferenceData.entryPoints
          ? membershipInvitationExtractMeetLinkFromConferenceData(calendarEvent.conferenceData)
          : null;
        if (!meetLink) {
          membershipInvitationLog("Warnung: Google Meet Link konnte nicht extrahiert werden.", true);
        }
        membershipInvitationSendInvitations(date, meetLink || "Kein Meet-Link verfügbar");
      }
    });
    membershipInvitationLog("Skript beendet");
  } catch (error) {
    membershipInvitationLog("FEHLER im Hauptprozess: " + error.message, true);
  }
}

// =========================
// Hilfsfunktionen
// =========================

function membershipInvitationGetUpcomingAssemblyDates(year, todayReference) {
  try {
    return MEMBERSHIPINVITATION_ASSEMBLY_DATES
      .map(dateStr => {
        const [day, month] = dateStr.split('.').map(Number);
        return new Date(year, month - 1, day);
      })
      .filter(date => date >= (todayReference || new Date()));
  } catch (error) {
    membershipInvitationLog("FEHLER beim Ermitteln der Versammlungsdaten: " + error.message, true);
    return [];
  }
}

function membershipInvitationCreateCalendarEvent(meetingDate, meetingNumber) {
  try {
    if (typeof Calendar === 'undefined' || !Calendar.Events) {
      throw new Error("Advanced Calendar API ist nicht aktiviert oder 'Calendar' ist nicht definiert.");
    }
    const startDateTime = new Date(meetingDate.getTime());
    startDateTime.setHours(MEMBERSHIPINVITATION_START_HOUR, MEMBERSHIPINVITATION_START_MINUTE, 0, 0);

    const endDateTime = new Date(meetingDate.getTime());
    endDateTime.setHours(MEMBERSHIPINVITATION_END_HOUR, MEMBERSHIPINVITATION_END_MINUTE, 0, 0);

    const eventResource = {
      summary: membershipInvitationApplyTemplate(MEMBERSHIPINVITATION_EVENT_SUMMARY_TEMPLATE, { meetingNumber }),
      description: MEMBERSHIPINVITATION_EVENT_DESCRIPTION,
      start: {
        dateTime: startDateTime.toISOString(),
        timeZone: "Europe/Berlin"
      },
      end: {
        dateTime: endDateTime.toISOString(),
        timeZone: "Europe/Berlin"
      },
      conferenceData: {
        createRequest: {
          requestId: `meet-${meetingNumber}-${new Date().getTime()}`,
          conferenceSolutionKey: {
            type: "hangoutsMeet"
          }
        }
      }
    };

    const createdEvent = Calendar.Events.insert(eventResource, MEMBERSHIPINVITATION_CALENDAR_ID, { conferenceDataVersion: 1 });
    membershipInvitationLog(`Kalenderevent erstellt: ${createdEvent.id}`);
    return createdEvent;
  } catch (error) {
    membershipInvitationLog("FEHLER beim Erstellen des Kalendereignisses: " + error.message, true);
    return null;
  }
}

function membershipInvitationExtractMeetLinkFromConferenceData(conferenceData) {
  if (!conferenceData || !conferenceData.entryPoints) return null;
  for (let ep of conferenceData.entryPoints) {
    if (ep.entryPointType === "video" && ep.uri) {
      return ep.uri;
    }
  }
  return null;
}

function membershipInvitationSendInvitations(meetingDate, meetLink) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(MEMBERSHIPINVITATION_SHEET_NAME);
    if (!sheet) {
      throw new Error(`Tabelle '${MEMBERSHIPINVITATION_SHEET_NAME}' nicht gefunden.`);
    }
    const data = sheet.getDataRange().getValues();
    const headers = data[0];
    const akzeptiertIndex = headers.indexOf(MEMBERSHIPINVITATION_HEADER_ACCEPTED);
    const emailIndex = headers.indexOf(MEMBERSHIPINVITATION_HEADER_EMAIL);

    if (akzeptiertIndex === -1 || emailIndex === -1) {
      throw new Error(`Die erforderlichen Spalten '${MEMBERSHIPINVITATION_HEADER_ACCEPTED}' oder '${MEMBERSHIPINVITATION_HEADER_EMAIL}' fehlen.`);
    }

    let invitationSent = false;
    const filterEmail = (MEMBERSHIPINVITATION_FILTER_EMAIL || "").trim();
    const filterActive = filterEmail.length >= 3;

    for (let i = 1; i < data.length; i++) {
      const row = data[i];
      const akzeptiert = row[akzeptiertIndex];
      const email = (row[emailIndex] || "").trim();

      if (filterActive) {
        if (akzeptiert === "Ja" && email.toLowerCase() === filterEmail.toLowerCase()) {
          membershipInvitationLog(`Filter aktiv: Einladung nur an ${email}`);
          const subject = membershipInvitationApplyTemplate(MEMBERSHIPINVITATION_EMAIL_SUBJECT_TEMPLATE, {
            STAR_EMOJI: MEMBERSHIPINVITATION_STAR_EMOJI,
            MEETING_DATE: Utilities.formatDate(meetingDate, Session.getScriptTimeZone(), "dd.MM.yyyy"),
            CLUB_NAME: MEMBERSHIPINVITATION_CLUB_NAME
          });
          const body = membershipInvitationApplyTemplate(MEMBERSHIPINVITATION_EMAIL_BODY_TEMPLATE, {
            MEETING_DATE: Utilities.formatDate(meetingDate, Session.getScriptTimeZone(), "dd.MM.yyyy"),
            MEET_LINK: meetLink,
            EMAIL_SIGNATURE: MEMBERSHIPINVITATION_EMAIL_SIGNATURE
          });
          membershipInvitationSendEmail(email, subject, body);
          membershipInvitationLog(`Gezielte Einladung gesendet an: ${email}`);
          invitationSent = true;
          break;
        }
      } else {
        if (akzeptiert === "Ja" && email) {
          const subject = membershipInvitationApplyTemplate(MEMBERSHIPINVITATION_EMAIL_SUBJECT_TEMPLATE, {
            STAR_EMOJI: MEMBERSHIPINVITATION_STAR_EMOJI,
            MEETING_DATE: Utilities.formatDate(meetingDate, Session.getScriptTimeZone(), "dd.MM.yyyy"),
            CLUB_NAME: MEMBERSHIPINVITATION_CLUB_NAME
          });
          const body = membershipInvitationApplyTemplate(MEMBERSHIPINVITATION_EMAIL_BODY_TEMPLATE, {
            MEETING_DATE: Utilities.formatDate(meetingDate, Session.getScriptTimeZone(), "dd.MM.yyyy"),
            MEET_LINK: meetLink,
            EMAIL_SIGNATURE: MEMBERSHIPINVITATION_EMAIL_SIGNATURE
          });
          membershipInvitationSendEmail(email, subject, body);
          membershipInvitationLog(`Einladung gesendet an: ${email}`);
          invitationSent = true;
        } else {
          membershipInvitationLog(`Mitglied ${email} hat nicht akzeptiert oder keine E-Mail hinterlegt und wird nicht eingeladen.`);
        }
      }
    }

    if (filterActive && !invitationSent) {
      membershipInvitationLog(`Filter aktiv: Keine passende akzeptierte E-Mail '${filterEmail}' in der Tabelle gefunden.`, true);
    }
    if (!filterActive && !invitationSent) {
      membershipInvitationLog("Keine Einladungen wurden verschickt, da keine akzeptierten Mitglieder mit E-Mail gefunden wurden.", true);
    }
  } catch (error) {
    membershipInvitationLog("FEHLER beim Versand der Einladungen: " + error.message, true);
  }
}

function membershipInvitationSendEmail(email, subject, body) {
  try {
    MailApp.sendEmail({
      to: email,
      subject: subject,
      htmlBody: body,
      from: MEMBERSHIPINVITATION_EMAIL_SENDER,
      replyTo: MEMBERSHIPINVITATION_MEMBERSHIP_DOCUMENTS_EMAIL_ADDRESS
    });
    membershipInvitationLog(`E-Mail an ${email} erfolgreich gesendet.`);
  } catch (error) {
    membershipInvitationLog(`FEHLER beim Senden der E-Mail an ${email}: ${error.message}`, true);
  }
}

function membershipInvitationApplyTemplate(template, values) {
  let result = template;
  for (let key in values) {
    const regex = new RegExp(`{{${key}}}`, 'g');
    result = result.replace(regex, values[key]);
  }
  return result;
}

function membershipInvitationLog(message, isError) {
  if (MEMBERSHIPINVITATION_LOGGING_ENABLED) {
    if (isError) {
      Logger.log("!!! " + message);
    } else {
      Logger.log(message);
    }
  }
}
