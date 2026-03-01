# Admin-Dashboard & Benutzerrechte

**Dokumentation:** Admin-Funktionen, Newsletter, Mitgliedsversammlungen

---

## Benutzerrollen & Rechte

### 1. Vorstand (Admin)
**Voller Zugriff auf alle Funktionen**

#### Mitgliederverwaltung
- • Alle Mitglieder sehen und bearbeiten
- • Neue Bewerbungen genehmigen/ablehnen
- • Mitgliedsstatus ändern
- • Mitgliedsbeiträge verwalten
- • Austritte verarbeiten

#### Ausschank
- • Ausschank durchführen
- • Limits überschreiben (in Ausnahmefällen)
- • Ausschank-History einsehen
- • Tagesabschluss durchführen

#### Inventar
- • Neue Chargen einbuchen
- • Bestand verwalten
- • Inventur durchführen
- • Lieferanten verwalten

#### Finanzen
- • Alle Transaktionen sehen
- • Spendenquittungen ausstellen
- • Finanzberichte erstellen
- • Steuerberater-Exporte generieren

#### Kommunikation
- • Newsletter an alle Mitglieder senden
- • Einzelne Mitglieder kontaktieren
- • Vorlage für E-Mails erstellen

#### Berichte
- • Alle Reports generieren
- • Behörden-Meldungen erstellen
- • Statistiken einsehen

---

### 2. Mitarbeiter (Staff)
**Eingeschränkter Zugriff für tägliche Arbeit**

#### Erlaubt
- • Ausschank durchführen
- • Mitgliedsstatus einsehen
- • Neue Mitglieder registrieren (nur Formular, keine Genehmigung)
- • Bestand einsehen
- • Eigene Schicht-Ausschänke verwalten

#### Nicht erlaubt
- • Mitgliedsbeiträge einsehen
- • Finanzberichte
- • Einstellungen ändern
- • Andere Mitarbeiter verwalten
- • Limits überschreiben

---

### 3. Mitglied (Member)
**Nur eigene Daten**

#### Erlaubt
- • Eigenes Profil bearbeiten
- • Eigenen Verbrauch einsehen
- • Mitgliedsausweis herunterladen
- • Kontaktdaten aktualisieren
- • Kündigung einreichen

#### Nicht erlaubt
- • Andere Mitglieder sehen
- • Ausschank durchführen
- • Irgendwelche Admin-Funktionen

---

## Admin-Dashboard - Neuanmeldungen Prüfen

### Dashboard für Neuanmeldungen (Vorstand & Mitarbeiter)

```
┌─────────────────────────────────────────────┐
│  🔔 Neuanmeldungen prüfen                   │
├─────────────────────────────────────────────┤
│                                             │
│  Status-Filter:                             │
│  [Alle] [Ausstehend] [In Bearbeitung]      │
│  [Angenommen] [Abgelehnt]                  │
│                                             │
│  📋 Offene Anträge (12)                     │
│                                             │
│  ┌─────────┬──────────┬───────┬──────────┐ │
│  │ Antrag  │ Name     │ Datum │ Status   │ │
│  ├─────────┼──────────┼───────┼──────────┤ │
│  │ #2024-1 │ Max M.   │ 28.02 │ 🟡 Neu   │ │
│  │ #2024-2 │ Lisa S.  │ 27.02 │ 🔵 Prüf. │ │
│  │ #2024-3 │ Tom B.   │ 26.02 │ 🟡 Neu   │ │
│  └─────────┴──────────┴───────┴──────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

### Detail-Ansicht eines Antrags

```
Antrag #2024-001 - Max Mustermann
Eingegangen: 28.02.2026 14:30
Status: 🟡 Ausstehend

┌─────────────────────────────────────────────┐
│ Schritt 1: Anmeldedaten ✅                 │
│ Schritt 2: Persönliche Daten ✅            │
│ Schritt 3: Adresse & Kontakt ✅            │
│ Schritt 4: Vereinsbezogene Daten ✅        │
│ Schritt 5: Einverständnisse ✅             │
└─────────────────────────────────────────────┘

Persönliche Daten:
• Name: Max Mustermann
• Geburtstag: 15.03.1990 (35 Jahre)
• Geburtsort: Leipzig
• Staatsangehörigkeit: Deutsch
• Ausweis: PA123456 (hochgeladen)

Adresse:
• Musterstraße 123
• 12345 Leipzig
• Seit: 01.01.2020

Kontakt:
• E-Mail: max@example.com
• Telefon: +49 123 456789

Vereinsbezogen:
• Geworben durch: Freunde
• Arbeitsstunden: Ja (Gießen, Ernte)
• Notfallkontakt: Anna Mustermann (Frau)

Prüfung:
[ ] Ausweis geprüft
[ ] Wohnsitz bestätigt
[ ] Keine roten Flaggen
[ ] Zuverlässigkeit OK

Notizen:
[Textfeld für interne Notizen]

Aktionen:
[✅ Annehmen]  [❌ Ablehnen]  [❓ Nachfragen]
```

### Rollen bei der Prüfung

| Aktion | Vorstand | Mitarbeiter |
|--------|----------|-------------|
| Anträge sehen | ✅ | ✅ |
| Details prüfen | ✅ | ✅ |
| Notizen hinzufügen | ✅ | ✅ |
| Annehmen/Ablehnen | ✅ | ❌ |
| Nachfragen senden | ✅ | ✅ |
| Final genehmigen | ✅ | ❌ |

**Workflow:**
1. Mitarbeiter prüft Antrag → Notizen → Empfehlung
2. Vorstand prüft Empfehlung → Entscheidung
3. System sendet E-Mail

---

## Admin-Dashboard

### Übersicht (Widgets)
```
┌─────────────────────────────────────────────┐
│  CSC-Admin Dashboard                        │
├─────────────────────────────────────────────┤
│  📊 Statistiken Heute                       │
│  • Ausschänke: 23 (1.247g)                 │
│  • Aktive Mitglieder: 342                  │
│  • Offene Bewerbungen: 5                   │
│                                             │
│  ⚠️ Wichtige Hinweise                       │
│  • 3 Mitglieder in Probezeit (bereit für  │
│    ersten Zugang)                          │
│  • Mitgliedslimit: 342/500 (68%)           │
│  • Nächste MV: 15.03.2026 (in 15 Tagen)   │
│                                             │
│  📦 Inventar Status                         │
│  • Critical: 2 Sorten fast ausverkauft     │
│  • Letzte Inventur: 12 Tage her            │
└─────────────────────────────────────────────┘
```

### Navigation
- **Dashboard** (Home)
- **Mitglieder** (Verwaltung)
- **Ausschank** (POS-System)
- **Inventar** (Bestand)
- **Finanzen** (Buchhaltung)
- **Mitgliedsversammlungen**
- **Newsletter**
- **Berichte** (Compliance)
- **Einstellungen**

---

## Newsletter-System

### Newsletter erstellen
- • Rich-Text Editor (WYSIWYG)
- • Bilder hochladen
- • Links einfügen
- • Empfänger auswählen:
  - Alle Mitglieder
  - Nur aktive Mitglieder
  - Nur Vorstand
  - Nur Probezeit-Mitglieder
  - Manuelle Auswahl

### Versand-Optionen
- • Sofort senden
- • Zeitgesteuert senden (z.B. Montag 10:00)
- • Als Entwurf speichern

### Empfänger-Statistik
- • Anzahl Empfänger
- • Öffnungsrate (wer hat geöffnet?)
- • Klickrate (wer hat Links geklickt?)
- • Bounces (nicht zustellbar)

### Newsletter-Typen
**Regelmäßige Newsletter:**
- • Monatlicher Club-Newsletter
- • Sorten-Updates (neue Chargen)
- • Veranstaltungen/Events
- • Wichtige Änderungen

**Beispiel-Template:**
```
Betreff: 🌿 CSC-Newsletter März 2026

Hallo [Vorname],

hier die aktuellen Neuigkeiten aus unserem Club:

🆕 Neue Sorten verfügbar:
• Blue Dream (THC: 18%, CBD: 0.5%)
• Northern Lights (THC: 20%, CBD: 0.3%)

📅 Nächste Termine:
• Mitgliedsversammlung: 15.03.2026
• Sprechstunde Vorstand: Jeden Dienstag 18-20h

💡 Wichtiger Hinweis:
Bitte denkt an eure monatlichen Limits!

Euer Vorstand
```

---

## Mitgliedsversammlungen (MV)

### MV verwalten
- • Neue MV planen
- • Datum und Uhrzeit
- • Ort (oder Online-Link)
- • Tagesordnungspunkte (TOPs)
- • Einladungsfrist (z.B. 2 Wochen vorher)

### Automatische Einladungen
**Trigger:** X Tage vor MV
**Empfänger:** Alle Mitglieder

**E-Mail:**
```
Betreff: Einladung zur Mitgliedsversammlung am [Datum]

Liebe Mitglieder,

hiermit laden wir euch herzlich zur nächsten
Mitgliedsversammlung ein:

📅 Datum: [Datum]
🕐 Uhrzeit: [Zeit]
📍 Ort: [Ort/Online-Link]

Tagesordnung:
1. Begrüßung
2. Feststellung der Beschlussfähigkeit
3. Genehmigung des Protokolls der letzten MV
4. Bericht des Vorstands
5. Kassenbericht
6. Entlastung des Vorstands
7. Neuwahlen
8. Verschiedenes

Bitte bestätigt eure Teilnahme bis [Datum].

Mit freundlichen Grüßen
Der Vorstand
```

### MV-Protokoll
- • Protokoll-Vorlage
- • Anwesenheitsliste
- • Beschlüsse dokumentieren
- • Abstimmungsergebnisse
- • Protokoll als PDF exportieren

### Erinnerungen
- • 1 Woche vorher: Erinnerung an Einladung
- • 1 Tag vorher: Final reminder
- • Nach MV: Protokoll versenden

### Historie
- • Alle vergangenen MVs
- • Protokolle archivieren
- • Beschlüsse durchsuchbar

---

## Schnellzugriff-Funktionen

### "Häufige Aktionen" (Shortcuts)
- • Neues Mitglied registrieren
- • Schnell-Ausschank
- • Newsletter senden
- • MV einladen
- • Tagesabschluss

### Suchfunktion
- • Global-Suche über alles
- • Mitglieds-Suche (Name, Nummer, E-Mail)
- • Chargen-Suche
- • Transaktions-Suche

### Notifications
- • Bell-Icon mit Badge (ungelesene)
- • Wichtige Ereignisse:
  - Neue Bewerbung
  - Mitglied erreicht Limit
  - Kritisch niedriger Bestand
  - MV steht an

---

## Mobile Ansicht

### Responsive Design
- • Dashboard funktioniert auf allen Geräten
- • Touch-optimiert
- • Kompakte Ansicht für Smartphones

### Mobile-App (optional später)
- • Nur für Mitglieder (Info, Ausweis)
- • Push-Notifications
- • Kein Ausschank per App!

---

## UI-Mockups (TODO)

*Screenshots/Wireframes für:*
- • Dashboard-Übersicht
- • Newsletter-Editor
- • MV-Planung
- • Benutzerrechte-Verwaltung

---

**Verwandte Dokumente:**
- [16-mitgliedschafts-workflow.md](./16-mitgliedschafts-workflow.md) - Anmelde-Prozess
- [96-gesetzliche-pflicht-features.md](./96-gesetzliche-pflicht-features.md) - Compliance