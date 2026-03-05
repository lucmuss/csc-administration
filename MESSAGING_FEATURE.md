# Massen-E-Mail Feature

## Übersicht

Das Massen-E-Mail-Feature ermöglicht das Versenden von E-Mails an alle Mitglieder oder ausgewählte Gruppen des Cannabis Social Clubs.

## Features

### E-Mail-Gruppen
- Gruppen erstellen, bearbeiten und löschen
- Mitglieder zu Gruppen hinzufügen/entfernen
- "Alle Mitglieder" als Standard-Gruppe

### Massen-E-Mails
- Markdown-Editor für E-Mail-Inhalt
- Personalisierung mit Variablen:
  - `{{ first_name }}` - Vorname
  - `{{ last_name }}` - Nachname
  - `{{ email }}` - E-Mail-Adresse
  - `{{ member_number }}` - Mitgliedsnummer
- Drei Empfänger-Modi:
  1. Alle registrierten Mitglieder
  2. Bestimmte Gruppe
  3. Individuelle Auswahl
- Vorschau vor Versand
- Tracking (gesendet, geöffnet, fehlgeschlagen)

### Google Analytics
- Tracking-ID über Umgebungsvariable `GA_TRACKING_ID`
- Anonymisierte IP-Adressen
- Nur aktiviert wenn Tracking-ID gesetzt

### Dev-Login für Tests
- URL: `/accounts/dev-login/`
- Nur bei `DEBUG=True` verfügbar
- Nutzt `TEST_USER_EMAIL` aus `.env`

## Verwendung

### Navigation
```
/messaging/           # Dashboard
/messaging/groups/    # Gruppen-Liste
/messaging/emails/    # E-Mail-Liste
```

### E-Mail versenden
1. "Neue E-Mail" klicken
2. Betreff und Inhalt (Markdown) eingeben
3. Empfänger auswählen (alle/Gruppe/individuell)
4. Vorschau prüfen
5. "Jetzt senden" klicken

### Screenshots erstellen
```bash
cd /home/node/.openclaw/workspace/projects/web/csc-administration
python scripts/generate_gui_screenshots.py
```

Screenshots werden in `output/gui-screenshots/` gespeichert.

## Technische Details

### Models
- `EmailGroup` - Gruppen-Verwaltung
- `EmailGroupMember` - Zuordnung Member <-> Gruppe
- `MassEmail` - E-Mail mit Status und Statistiken
- `EmailLog` - Einzelne Versand-Logs mit Tracking

### Celery-Task
- `send_mass_email_task` - Asynchroner Versand
- Rate-Limiting (0.1s Pause zwischen Mails)
- Fehler-Handling mit Retry

### Tracking
- 1x1 Pixel GIF für Öffnungs-Tracking
- IP-Adresse und User-Agent werden gespeichert
- DSGVO-konform (Anonymisierung)

## Umgebungsvariablen

```bash
# Google Analytics (optional)
GA_TRACKING_ID=G-XXXXXXXXXX

# Test-User für Dev-Login
TEST_USER_EMAIL=test@example.com
```

## Admin-Interface

Alle Models sind im Django-Admin verfügbar unter:
```
/admin/messaging/
```
