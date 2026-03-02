# CSC Admin – System Requirements

> Cannabis Social Club Verwaltungssystem  
> Projekt: `projects/csc-app/`  
> Daten: `cdata/` (JSON-Templates)

---

## 1. Übersicht

Verwaltungssystem für einen Cannabis Social Club (CSC) nach dem neuen CanG (Cannabisgesetz). Ermöglicht Mitgliederverwaltung, Bestellabwicklung, Abgabe-Tracking und Inventarverwaltung mit voller DSGVO-Konformität.

---

## 2. Kernfunktionen

### 2.1 Mitgliederverwaltung
- **Mitglieder-Import**: CSV/Excel-Import aus Google Forms oder anderen Quellen
- **Telefonnummer-Normalisierung**: Automatisch "+" → "00", als String speichern (Excel-kompatibel)
- **Verifikations-Workflow**: Altersprüfung (21+), Wohnsitzverifizierung, Ausschluss anderer CSCs
- **Status-Tracking**: Antrag → Akzeptiert → Verifiziert → Aktiv
- **Abgabelimits**: 50g/Monat, 25g/Tag (gesetzlich vorgeschrieben)
- **Guthaben-Verwaltung**: Kontostand für Vorauszahlungen
- **8-Wochen-Deadline**: Automatisches Tracking der Registrierungsfrist (Antrag → Unterlagen vollständig)
- **Farbmarkierung**: Visuelle Statusanzeige (z.B. blau = neu, grün = aktiv, rot = Problem)

### 2.2 Bestellsystem
- **Sorten-Auswahl**: Blüten und Stecklinge mit Live-Bestand
- **Warenkorb**: Automatische Limit-Prüfung (Monats- und Tageslimits)
- **Zahlung**: Bar, Überweisung oder Lastschrift (SEPA)
- **Ausgabe-Planung**: Monatliche Verteilungstermine

### 2.3 Inventar & Abgabe
- **Chargen-Tracking**: Herkunft, Erntedatum, Qualitätsgrade
- **THC/CBD-Erfassung** (Kritisch!): Pflichtfeld bei jeder Charge (Infozettel-Pflicht CanG)
- **Abgabe-Logging**: Zeitstempel, Menge, verbleibende Limits
- **Compliance-Reports**: Nachweis für Behörden

### 2.4 Finanzen
- **Zahlungs-Tracking**: Offene Posten, eingegangene Zahlungen
- **USt-Split** (Kritisch!): Automatisch 7% (Cannabis-Abgabe) vs 19% (Merchandise/Services)
- **SEPA-Lastschrift**: Mandatsverwaltung, automatische Abbuchung
- **Buchhaltung**: Export für Steuerberater (DATEV-konform)

### 2.5 Bulk-Operations (Massenverarbeitung)
- **Mehrfachbearbeitung**: Auswahl mehrerer Mitglieder für gemeinsame Aktionen
- **CSV-Export gefilterter Listen**: Mit aktuellen Filtern und Sichtbarkeiten
- **Massen-E-Mail**: An Mitgliedersegmente (z.B. alle mit offenen Zahlungen)
- **Status-Änderungen**: Mehrere Mitglieder gleichzeitig aktivieren/deaktivieren
- **Rollen-Zuweisung**: Bulk-Zuweisung von Berechtigungen

### 2.5 Rollen- & Rechtesystem (RBAC)

#### Rollen-Hierarchie
```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM-ADMINISTRATOR                     │
│                    (technischer Zugriff)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     GESCHÄFTSFÜHRER                         │
│              (Vollzugriff auf alle Clubs)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐  ┌────────▼────────┐  ┌──────▼──────┐
│   VORSTAND   │  │    KASSIERER    │  │  MITARBEITER │
│  (1. Vors.,  │  │  (Finanzen,     │  │  (Support,   │
│   2. Vors.,  │  │   Zahlungen,    │  │   Logistik,  │
│   Schriftf.) │  │   Buchhaltung)  │  │   Events)    │
└───────┬──────┘  └────────┬────────┘  └──────┬──────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │   MITGLIED  │
                    │  (nur Lesen)│
                    └─────────────┘
```

#### Berechtigungs-Matrix

| Funktion | System-Admin | GF | Vorstand | Kassierer | Mitarbeiter | Mitglied |
|----------|-------------|----|----------|-----------|-------------|----------|
| **Mitglieder** |
| Antrag ansehen | ✅ | ✅ | ✅ | ❌ | ❌ | Eigen |
| Mitglieder akzeptieren | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Mitglieder verifizieren | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Mitglieder deaktivieren | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Bankdaten sehen | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Finanzen** |
| Zahlungen erfassen | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| SEPA-Lastschrift ausführen | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Berichte exportieren | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Preise ändern | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Bestellungen** |
| Bestellungen sehen | ✅ | ✅ | ✅ | ✅ | ✅ | Eigen |
| Bestellungen bearbeiten | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Ausgabe bestätigen | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Kommunikation** |
| E-Mails senden | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Mitgliederversammlung einberufen | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Newsletter versenden | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **System** |
| Einstellungen ändern | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Benutzer verwalten | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Logs einsehen | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Backups erstellen | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

#### Wichtige Regeln (aus Satzung § 3)
- **Nur Vorstand** darf Mitglieder aufnehmen (einfache Mehrheit)
- **Kündigungsfrist**: 2 Monate zum Ende der Mitgliedschaft
- **Max. Mitglieder**: 500 pro Club
- **Mindestmitgliedschaft**: 3 Monate
- **Keine Doppelmitgliedschaft** in anderen CSCs

### 2.6 Präventionsmodul (Suchtprävention)

#### Konsum-Muster-Analyse
```
PRÜFUNGSKRITERIEN:
├── Häufigkeit
│   ├── Tägliche Bestellungen (>20 Tage/Monat)
│   ├── Steigende Mengen (+30% zum Vormonat)
│   └── Frühzeitige Nachbestellung
│
├── Muster
│   ├── Konstanter hoher Verbrauch (>40g/Monat)
│   ├── Nacht-Bestellungen (22:00-06:00)
│   └── Mehrfachbestellungen pro Tag
│
└── Risikoindikatoren
    ├── Mehrere CSC-Mitgliedschaften
    ├── Unvollständige Angaben
    └── Zahlungsrückstände
```

#### Eskalationsstufen
| Stufe | Kriterium | Aktion | Benachrichtigung |
|-------|-----------|--------|------------------|
| 🟡 **Aufmerksam** | 2+ Indikatoren | Markierung im System | Interne Notiz |
| 🟠 **Gespräch** | 4+ Indikatoren oder >45g/Monat | Persönliches Gespräch | Vorstand |
| 🔴 **Prävention** | 6+ Indikatoren oder >50g/Monat | Zwangsberatung | Vorstand + Beratungsstelle |
| ⚫ **Ausschluss** | Wiederholte Verstöße | Mitgliedschaft beenden | Vorstand |

#### Automatische Maßnahmen
- **Wöchentliche Reports** an Vorstand mit auffälligen Mitgliedern
- **Monatliche Auswertung**: Durchschnittskonsum, Trends
- **Automatische Warnung** bei Überschreitung von 40g/Monat
- **Suchtberatungs-Hotline** verlinken im Mitgliederbereich

### 2.7 Multi-Tenant Architektur

#### Club-Verwaltung
```
PLATTFORM
├── Club 1: CSC Leipzig Süd
│   ├── Eigene Mitglieder
│   ├── Eigene Sorten/Preise
│   ├── Eigene Vorstände
│   └── Eigene Einstellungen
│
├── Club 2: CSC Berlin Mitte
│   ├── Eigene Mitglieder
│   ├── Eigene Sorten/Preise
│   └── ...
│
└── Club 3: [Weiterer Club]
    └── ...
```

#### White-Label Features
- **Logo-Upload** für jeden Club
- **Farbschema** anpassbar (Primary, Secondary)
- **E-Mail-Templates** pro Club individualisierbar
- **Domain-Mapping** (optional: club.csc-platform.de)
- **Eigene Bankverbindung** pro Club
- **Eigene Satzung** hinterlegbar

### 2.8 Admin-Dashboard Einstellungen

#### System-Einstellungen (nur System-Admin)
```yaml
Datenbank:
  - Backup-Zeitplan (täglich/wöchentlich)
  - Aufbewahrungsfrist (min. 2 Jahre laut CanG)
  - Verschlüsselung aktivieren

Sicherheit:
  - 2FA für alle Admin-Benutzer
  - Passwort-Richtlinien
  - Session-Timeout
  - IP-Whitelist

Monitoring:
  - Fehlerprotokolle
  - Performance-Metriken
  - API-Rate-Limits
```

#### Club-Einstellungen (Vorstand)
```yaml
Mitgliedschaft:
  Aufnahmegebühr: 20 EUR
  Monatsbeitrag Standard: 24 EUR
  Mindestmitgliedschaft: 3 Monate
  Max. Mitglieder: 500
  
Abgabelimits:
  Tageslimit: 25g
  Monatslimit: 50g
  
Sorten & Preise:
  - Orange Bud: 8 EUR/g
  - Sage n Sour: 9 EUR/g
  - [Weitere Sorten...]
  
Prävention:
  Warnschwelle: 40g/Monat
  Beratungspflicht: 45g/Monat
  
Automatisierung:
  Limit-Reset: täglich 00:00
  Mahnungen: nach 7 Tagen
  Inaktivitäts-Erinnerung: nach 60 Tagen
  
Kommunikation:
  Absender-E-Mail: info@csc-leipzig.eu
  SMTP-Server: [konfigurierbar]
  Newsletter-Provider: [optional]
```

#### Benachrichtigungs-Einstellungen (pro Rolle)
```yaml
Vorstand:
  - Neuer Mitgliedsantrag: sofort
  - Überschreitung Präventionsschwelle: sofort
  - Zahlungsrückstand: täglich
  - Mitgliederversammlung anstehend: 6 Tage vorher

Kassierer:
  - Neue Zahlung eingegangen: sofort
  - SEPA-Lastschrift fehlgeschlagen: sofort
  - Monatlicher Finanzreport: 1. des Monats

Mitarbeiter:
  - Neue Bestellung: sofort
  - Inventar niedrig: täglich
  - Ausgabe-Termin morgen: 1 Tag vorher
```

### 2.9 Automatisierung & Workflows (aus Appscripts)
```
1. Antragseingang (Google Form)
   ↓
2. Automatische Prüfung:
   - Duplikat-Check (E-Mail)
   - Altersprüfung (21+)
   - Mitgliedsnummer-Vergabe (automatisch fortlaufend)
   - Beitrittsdatum = 1. des Folgemonats
   ↓
3. Status-Setzung:
   - Akzeptiert: "Nein"
   - Verifiziert: "Nein"
   - Zahlung: "Nein"
   - Guthaben: 0€
   - Monatsabgabe: 50g
   - Tagesabgabe: 25g
   ↓
4. E-Mail mit Dokumenten:
   - Aufnahmeantrag (PDF)
   - SEPA-Lastschriftmandat (PDF)
   - Selbstauskunft (PDF)
   - Mitgliederausweis (PDF)
   ↓
5. Manuelle Prüfung durch Vorstand
   ↓
6. Freischaltung (Akzeptiert + Verifiziert)
```

#### Dokumenten-Generierung
**Templates mit Platzhaltern:**
- `{{vorname}}` - Vorname
- `{{nachname}}` - Nachname
- `{{geburtsdatum}}` - Geburtsdatum
- `{{strasse}}` - Straße, Hausnummer
- `{{postleitzahl}}` - PLZ
- `{{stadt}}` - Stadt
- `{{telefonnummer}}` - Telefon
- `{{email}}` - E-Mail
- `{{aufnahmedatum}}` - Aufnahmedatum
- `{{mitgliedsnummer}}` - Mitgliedsnummer
- `{{kreditinstitut}}` - Bank
- `{{bic}}` - BIC
- `{{iban}}` - IBAN
- `{{beitrittsdatum}}` - Beitrittsdatum
- `{{datenschutzhinweis_checkbox}}` - [x] wenn akzeptiert
- `{{keinmitglied_checkbox}}` - [x] wenn kein anderer CSC
- `{{lebensjahr_checkbox}}` - [x] wenn 21+
- `{{wohnsitz_checkbox}}` - [x] wenn DE
- `{{lichtbild_checkbox}}` - [x] wenn Ausweis vorhanden

**Dokumente:**
1. **Aufnahmeantrag** - Mitgliedschaftsvertrag
2. **SEPA-Lastschriftmandat** - Lastschrift-Einwilligung
3. **Selbstauskunft** - Persönliche Erklärung
4. **Mitgliederausweis** - Ausweis für das Mitglied

#### Mitgliederversammlungen
- **Termine**: Vierteljährlich (01.01., 01.04., 01.07., 01.10.)
- **Einladung**: 6 Tage vorher per E-Mail
- **Teilnehmer**: Nur akzeptierte und verifizierte Mitglieder
- **Format**: Google Meet (Video-Konferenz)
- **Dauer**: 19:00 - 21:00 Uhr
- **Features**:
  - Automatischer Kalendereintrag
  - Meet-Link-Generierung
  - Protokoll-Ordner (Google Drive)
  - Abstimmungsberechtigung nur für vollständige Mitglieder
  - Ausweis-Check per Kamera zu Beginn

#### Limit-Reset-Automatik
```
TÄGLICH (z.B. 00:00 Uhr):
- Tagesabgabe aller Mitglieder auf 25g zurücksetzen

MONATLICH (am 1. des Monats):
- Monatsabgabe aller Mitglieder auf 50g zurücksetzen
```

#### Inaktivitäts-Benachrichtigung
- **Trigger**: 60 Tage ohne Bestellung
- **Bedingungen**:
  - Mitglied akzeptiert: Ja
  - Mitglied verifiziert: Ja
  - Optionaler Newsletter: Ja
- **Inhalt**: Erinnerung mit aktuellem Sortenangebot
- **Links**: Bestellformular, FAQ

### 2.6 E-Mail-Kommunikation

#### Standard-E-Mail-Format
```
Betreff: ✨ [Betreff] - CSC Leipzig Süd e.V.

[Inhalt]

--
Zusätzliche Kontaktinformationen:
Cannabis Social Club Leipzig Süd e.V.
Postfach 35 03 04
04165 Leipzig
info@csc-leipzig.eu
+4917643291439
```

#### E-Mail-Templates
1. **Mitgliedschaftsantrag eingegangen**
   - Bestätigung des Antrags
   - Anhang: 4 PDF-Dokumente
   - Hinweis: 8 Wochen Frist zur Registrierung
   - FAQ-Link

2. **Mitgliederversammlungseinladung**
   - Termin und Uhrzeit
   - Google Meet-Link
   - Hinweise zur Teilnahme (Technik, Ausweis)
   - Tagesordnungspunkte (1 Woche vorher einreichen)
   - Protokoll-Archiv

3. **Bestell-Erinnerung (Inaktivität)**
   - Freundliche Erinnerung
   - Aktuelles Sortenangebot
   - Direktlink zum Bestellformular

4. **Registrierung fehlgeschlagen**
   - Duplikat gefunden
   - Altersanforderung nicht erfüllt

#### PDF-Generierung (aus Templates)
- **Template-Engine**: Google Docs oder HTML → PDF
- **18 Platzhalter**: {{vorname}}, {{nachname}}, {{geburtsdatum}}, etc.
- **Dokumente**:
  1. Aufnahmeantrag
  2. SEPA-Lastschriftmandat
  3. Selbstauskunft
  4. Mitgliedsausweis
- **Anhang-Limit**: Max. 10 MB pro E-Mail (alle PDFs zusammen)

#### E-Mail-Threading
- **Konversationsverlauf**: Alle E-Mails zum Mitglied gruppiert
- **Antwort-Erkennung**: Automatische Zuordnung an Mitglied
- **Ticket-System**: Status "Offen", "Warte auf Antwort", "Geschlossen"

---

## 3. Datenmodell

### 3.1 Entitäten

```
Member (Mitglied)
├── Personal: name, birth_date, address, contact
├── Membership: number, join_date, status, limits

Backup-Strategie (Kritisch!)
├── Täglich: Automatisches Backup (02:00 Uhr)
├── Verschlüsselung: AES-256 vor Upload
├── Speicherort: Extern (nicht auf gleichem Server)
├── Aufbewahrung: 30 Tage Versionierung
├── Test: Monatliche Wiederherstellungs-Übung
├── Consent: privacy, sepa, age_verified, etc.
└── BankDetails: iban, bic, mandate (separate Tabelle)

Strain (Sorte)
├── Basic: name, type (flower/clone), price
├── Inventory: stock, batch_id, harvest_date
└── Details: thc, cbd, description

Order (Bestellung)
├── Meta: timestamp, status, distribution_month
├── Items: strains, quantities, prices
├── Payment: method, amount, status
└── Member: reference, limits_check

Distribution (Abgabe)
├── Log: timestamp, quantity, remaining_limits
├── Verification: id_check, signature
└── Audit: who, when, what

DSGVO-Automatisierung (Kritisch!)
├── Automatische Löschung: 2 Jahre nach Austritt (CanG-Frist)
├── Anonymisierung: Personenbezogene Daten entfernen
├── Finanzdaten: 10 Jahre getrennt aufbewahren (Steuerrecht)
├── Benachrichtigung: E-Mail 30 Tage vor Löschung
```

### 3.2 Daten-Dateien (cdata/)

| Datei | Inhalt | Format |
|-------|--------|--------|
| `member_template.json` | Beispiel-Mitglieder (anonymisiert) | JSON |
| `strains.json` | Verfügbare Sorten (Blüten + Stecklinge) | JSON |
| `order_template.json` | Beispiel-Bestellungen | JSON |

---

## 4. Import/Export

### 4.1 Mitglieder-Import

**Quelle**: Google Forms Excel-Export

**Erforderliche Spalten**:
```
- Zeitstempel (Excel-Datum)
- E-Mail-Adresse
- Aufnahmedatum
- Vorname, Nachname
- Geburtsdatum (Excel-Datum)
- Straße, PLZ, Stadt
- Telefonnummer
- Datenschutzerklärung (Ja/Nein)
- IBAN, BIC, Kreditinstitut
- Ermächtigung zur Lastschrift (Ja/Nein)
- Mitgliedschaft anderer Anbaugemeinschaften (Ja/Nein)
- Fester Wohnsitz in Deutschland (Ja/Nein)
- Mindestalter 21 Jahre (Ja/Nein)
- Aktueller Lichtbildausweis (Ja/Nein)
- Newsletter für wichtige Ankündigungen (Ja/Nein)
- Optionaler Newsletter (Ja/Nein)
- Mitgliedsnummer
- Monatsabgabe (Gramm, default: 50)
- Tagesabgabe (Gramm, default: 25)
- Beitrittsdatum
- Guthaben
- Akzeptiert (Ja/Nein)
- Verifiziert (Ja/Nein)
- Zahlung (Ja/Nein)
```

**Import-Skript**: `import_members.py`
- Konvertiert Excel-Daten in SQLite
- Validiert Pflichtfelder
- **IBAN-Validierung** (Kritisch!): Prüfziffer-Check vor Speicherung
- Trennt Bankdaten (DSGVO)
- Erkennt Duplikate
- **Fehlerbehandlung**: Rollback bei Fehlern (Transaktionssicherheit)

### 4.2 Export-Formate

- **Mitglieder**: CSV, JSON
- **Bestellungen**: CSV (monatlich)
- **Abgabe-Log**: CSV (Compliance)
- **Buchhaltung**: CSV, DATEV-Format

---

## 5. Technische Anforderungen

### 5.1 Backend
- **Datenbank**: SQLite (lokal) oder PostgreSQL (Server)
- **API**: REST oder GraphQL
- **Authentifizierung**: JWT, rollenbasiert (Admin, Vorstand, Mitglied)
- **Verschlüsselung**: AES-256 für Bankdaten

### 5.2 Frontend
- **Web**: React/Vue.js oder Django
- **Mobile**: React Native oder Flutter
- **Offline**: PWA mit lokaler Cache

### 5.3 Sicherheit
- **DSGVO**: Recht auf Löschung, Datenportabilität
- **Zugriffskontrolle**: 2FA für Admins
- **Audit-Log**: Alle Änderungen protokolliert
- **Backup**: Automatisch verschlüsselt

### 5.4 Logging-System
- **Konfigurierbar**: Logging an/aus schaltbar (für Performance/Entwicklung)
- **Strukturierte Logs**: Zeitstempel, Benutzer, Aktion, Details (JSON)
- **Level**: DEBUG, INFO, WARN, ERROR
- **Ziele**: Datei, Datenbank, externer Service (optional)
- **Retention**: Automatische Bereinigung nach 90 Tagen

### 5.5 Konfigurations-Management
- **Zentrale Config**: Keine Hardcoding, alle Werte konfigurierbar
- **Umgebungsvariablen**: .env-Datei für sensible Daten
- **Admin-Oberfläche**: Web-UI für Konfiguration ohne Code-Änderung
- **Validierung**: Config-Werte werden beim Speichern geprüft
- **Versionierung**: Änderungen werden protokolliert

---

## 6. Rechtliche Anforderungen

### 6.1 CanG (Cannabisgesetz)
- Abgabe nur an Mitglieder ab 21 Jahren
- Max. 50g/Monat, 25g/Tag pro Mitglied
- Keine Weitergabe an Dritte
- Dokumentationspflicht (2 Jahre)

#### Verdachtsanzeige (Automatisiert - Kritisch!)
- **Pflicht**: Bei Verdacht auf Weitergabe/Überkonsum an Behörde melden
- **Trigger** (automatisch):
  - >50g/Monat konsumiert (>100% des Limits)
  - >25g an einem Tag mehrfach hintereinander
  - Auffällige Bestellmuster (z.B. täglich genau 24,9g)
  - Mehrere CSC-Mitgliedschaften (Doppelmitgliedschaft)
  - Abholung durch unterschiedliche Personen (Bevollmächtigte wechseln häufig)
- **Automatisierung**:
  1. System erkennt Muster (Algorithmus)
  2. Alert an Vorstand + Sicherheitsbeauftragten
  3. Bei Bestätigung: Automatische PDF-Generierung der Verdachtsanzeige
  4. Versand an zuständige Behörde (Polizei/Landratsamt)
- **Datenschutz**: Nur pseudonymisierte Daten, keine Gesundheitsdaten
- **Frist**: Unverzüglich nach Erkennen des Verdachts

### 6.2 DSGVO (Minimal-Viable)

#### Datenminimierung (Reduziert)
- **Nur Stammdaten**: Name, Adresse, Alter, Kontakt
- **KEINE Konsumgewohnheiten**: Keine Speicherung von Vorlieben, Häufigkeiten, Mustern
- **KEINE Gesundheitsdaten**: Ohne explizite Einwilligung
- **Zweckbindung**: Daten nur für Vereinszweck verwenden

#### Einwilligung
- Checkbox bei Registrierung (nachweisbar speichern mit Zeitstempel)
- Jederzeit widerrufbar
- Getrennte Einwilligungen für: Mitgliedschaft, Newsletter, Datenverarbeitung

#### Selbstbedienung (DSGVO-Rechte)
- **Auskunft**: Mitglied kann eigene Daten einsehen (Profil-Export)
- **Berichtigung**: Selbst ändern im Profil
- **Löschung**: "Account löschen"-Button (nach 2 Jahren CanG-Frist)
- **Datenübertragbarkeit**: CSV-Export der eigenen Daten
- **KEIN Support-Ticket** nötig für Standard-Anfragen

#### Aufbewahrungsfristen (Minimal)
| Daten | Frist | Nach Ablauf |
|-------|-------|-------------|
| Mitgliedsdaten | 2 Jahre nach Austritt | Automatische Löschung |
| Finanzdaten | 10 Jahre (Steuerrecht) | Anonymisierung |
| Buchungsbelege | 10 Jahre | Archivierung (Papier) |
| Kommunikation | 2 Jahre | Löschung |

#### Breach-Notification (Kritisch!)
- Automatische Erkennung: >100 Failed Logins/h, Massen-Downloads
- Meldung binnen 72h an: Landesbeauftragte für Datenschutz + betroffene Mitglieder
- Nur bei echtem Datenleck (nicht bei jedem Fehlversuch)

### 6.3 SEPA
- Mandatsreferenz pro Mitglied
- Vorabankündigung (mind. 1 Tag)
- Mandat speicherbar (10 Jahre)

---

## 7. UI/UX Anforderungen

### 7.1 Dashboard
- Mitglieder-Statistiken (gesamt, aktiv, pending)
- Offene Bestellungen
- Inventar-Übersicht (niedriger Bestand)
- Zahlungsstatus

### 7.2 Mitglieder-Verwaltung
- Liste mit Filter (Status, PLZ, etc.)
- Detail-Ansicht mit allen Daten
- Verifikations-Workflow
- Guthaben-Verwaltung

### 7.3 Bestell-Prozess
- Einfache Sorten-Auswahl
- Live-Limit-Anzeige (Monat/Tages)
- Warenkorb mit Preisberechnung
- Checkout mit Zahlungsauswahl

### 7.4 Ausgabe-Station
- QR-Code-Scan für Mitgliedsausweis
- Automatische Limit-Prüfung
- Unterschrift per Touch/Stift
- Quittungsdruck

---

## 8. Integrationen

### 8.1 Zahlungsanbieter
- **SEPA**: Eigenes Mandatsmanagement
- **PayPal**: Optional für Vorauszahlungen
- **Krypto**: Optional (Bitcoin/Monero)

### 8.2 Kommunikation
- **E-Mail**: Versand über SMTP (Brevo, SendGrid)
- **SMS**: Für wichtige Benachrichtigungen
- **Telegram**: Bot für Status-Updates

### 8.3 Kalender
- **Google Calendar**: Ausgabetermine
- **iCal**: Export für Mitglieder

---

## 9. Reports & Statistiken

### 9.1 Mitglieder
- Wachstum (monatlich/jährlich)
- Aktivitätsrate
- Durchschnittliche Abgabe

### 9.2 Abgabe
- Sorten-Ranking
- Durchschnittliche Menge
- Auslastung pro Termin

### 9.3 Finanzen
- Umsatz pro Monat
- Offene Posten
- Zahlungsmethoden-Verteilung

---

## 10. Entwicklungs-Prioritäten

### Phase 1: MVP (Minimum Viable Product)
- [ ] Mitglieder-Import aus Excel
- [ ] Mitgliederverwaltung (CRUD)
- [ ] Bestellsystem (Web)
- [ ] Abgabe-Logging
- [ ] Basis-Reports

### Phase 2: Erweiterung
- [ ] Mobile App
- [ ] Zahlungsintegration
- [ ] QR-Code-System
- [ ] Newsletter-System
- [ ] API für externe Tools

### Phase 3: Professional
- [ ] Multi-Club-Support
- [ ] Erweiterte Analytics
- [ ] White-Label-Lösung
- [ ] Cloud-Hosting

---

## 13. MVP Definition (Minimal Viable Product)

### MVP-Philosophie
**Nicht alles auf einmal!** Fokus auf CanG-Konformität und operative Fähigkeit.

### Top 5 MVP-Features (MUST-HAVE)

| Rang | Feature | Begründung |
|------|---------|------------|
| 1 | **Mitgliederverwaltung mit Altersprüfung** | CanG: Mindestalter 21, Wohnsitz 6 Monate |
| 2 | **Limit-Prüfung (25g/Tag, 50g/Monat)** | CanG: Hard-Limits, automatische Durchsetzung |
| 3 | **Bestandsverwaltung & Chargenrückverfolgung** | CanG: Seed-to-Sale, 2 Jahre Dokumentation |
| 4 | **Präventions- & Jugendschutz-Management** | CanG: Pflichtkonzept, Beratung bei Abgabe |
| 5 | **Sicherheits- & Zutrittskontrolle** | CanG: Schutz vor unbefugtem Zugriff |

### MVP-Plus (SHOULD-HAVE für Launch)
- [ ] SEPA-Zahlung (für bargeldlosen Betrieb)
- [ ] Quittungssystem/Belegerstellung (für Transparenz)
- [ ] Jahresmeldung an Behörden (automatisiert)
- [ ] E-Mail-Kommunikation (Einladungen, Erinnerungen)

### POST-MVP (NACH Launch)
- [ ] Mobile App (PWA reicht erstmal)
- [ ] KI-Assistent (optional)
- [ ] Community-Features
- [ ] Erweiterte Analytics
- [ ] Multi-Tenant

### MVP-Timeline (Empfohlen)
| Phase | Dauer | Deliverable |
|-------|-------|-------------|
| Setup & Core | 4 Wochen | Django-Setup, Auth, Models |
| Mitgliedschaft | 3 Wochen | Registrierung, Verifizierung, Profile |
| Bestellung & Limits | 3 Wochen | Shop, Warenkorb, Limit-Prüfung |
| Compliance | 2 Wochen | CanG-Reports, Prävention |
| Testing & Launch | 2 Wochen | E2E-Tests, Bugfixes, Go-Live |
| **Gesamt** | **14 Wochen** | **MVP Ready** |

---

## 14. UI/UX Guidelines (für 50+ Zielgruppe)

### Barrierefreiheit

#### Kontrast & Lesbarkeit
- **WCAG AA Standard**: Kontrastverhältnis mindestens 4.5:1
- **Schriftgröße**: Mindestens 16px (besser 18px) für Fließtext
- **Schriftart**: Serifenlose Schrift (system-ui, sans-serif)
- **Zeilenabstand**: 1.5 für bessere Lesbarkeit
- **Kein helles Grau auf Weiß**: Verwende dunkles Grau (#333) statt Hellgrau (#999)

#### Visuelles Feedback
- **Erfolgsbestätigungen**: Text statt nur Farbe
  - ❌ "Button wird grün"
  - ✅ "Bestellung erfolgreich gespeichert"
- **Fehlermeldungen**: Konstruktiv und lösungsorientiert
  - ❌ "Fehler"
  - ✅ "E-Mail-Adresse ungültig. Bitte überprüfen Sie das Format."
- **Ladezustände**: Deutlich sichtbar (Spinner + Text "Wird geladen...")

#### Sprache & Terminologie
- **Kein Fachjargon**:
  - ❌ "Dashboard"
  - ✅ "Mein Bereich" / "Übersicht"
- **Keine Anglizismen** (wenn möglich):
  - ❌ "Checkout"
  - ✅ "Zur Kasse"
  - ❌ "Inventory"
  - ✅ "Vorrat"
- **Verständliche Begriffe**:
  - ❌ "CRUD-Operationen"
  - ✅ "Anlegen, Anzeigen, Bearbeiten, Löschen"

### Navigation & Orientierung

#### Konsistente Struktur
- **Navigation immer sichtbar**: Sticky Header
- **Breadcrumb**: Wo bin ich? (Home > Shop > Blue Dream)
- **Zurück-Button**: In jedem Formular
- **Startseite-Button**: Logo klickbar

#### Einfache Workflows
- **Maximal 3 Klicks** bis zur Zielaktion
- **Keine verschachtelten Menüs**: Maximal 1 Ebene
- **Klare Call-to-Action**: Ein primärer Button pro Seite
- **Fortschrittsanzeige**: Bei mehrstufigen Prozessen (Registrierung: Schritt 1 von 3)

### Formulare

#### Eingabefelder
- **Große Touch-Targets**: Mindestens 44x44px
- **Label immer sichtbar**: Nicht nur Placeholder
- **Feldvalidierung in Echtzeit**: Aber nicht zu aggressiv (nach Verlassen des Feldes)
- **Autofill unterstützen**: Name, Adresse, E-Mail

#### Bestätigungen
- **Wichtige Aktionen bestätigen**: "Möchten Sie wirklich löschen?"
- **Aber nicht zu viele**: Nur bei kritischen Aktionen (Löschen, Kündigen)

### Mobile Optimierung

#### Touch-Optimierung
- **Abstände zwischen Buttons**: Mindestens 8px
- **Keine Hover-States**: Touch hat kein Hover
- **Swipe-Gesten**: Optional, nicht Pflicht (Alternative immer sichtbar)

#### Performance
- **Ladezeit < 3 Sekunden**: Sonst Absprung
- **Progressive Loading**: Erst Text, dann Bilder
- **Offline-Indikator**: "Sie sind offline" anzeigen

### Test-Checkliste (vor Launch)
- [ ] Mit 60+ jährigen Testern ausprobieren
- [ ] Screenreader-Test (VoiceOver/TalkBack)
- [ ] Tastatur-Navigation testen (Tab-Taste)
- [ ] Kontrast-Checker (WebAIM)
- [ ] Mobile Geräte testen (iPhone, Android)

---

## 11. Datei-Struktur

```
projects/csc-app/
├── cdata/                          # Daten-Templates
│   ├── member_template.json        # Beispiel-Mitglieder
│   ├── strains.json                # Verfügbare Sorten
│   └── order_template.json         # Beispiel-Bestellungen
├── database_schema.sql             # SQL-Schema
├── import_members.py               # Import-Skript
└── REQUIREMENTS.md                 # Diese Datei
```

---

## 12. Hinweise für Entwickler

### 12.1 Excel-Import
- Excel-Datum: Float seit 30.12.1899
- Ja/Nein: Konvertieren zu Boolean
- IBAN: Leerzeichen entfernen
- Telefon: Nur Zahlen und +

### 12.2 Limit-Prüfung
```python
def check_limits(member_id, requested_amount):
    monthly_used = get_monthly_usage(member_id)
    daily_used = get_daily_usage(member_id)
    
    if monthly_used + requested_amount > MONTHLY_LIMIT:
        return False, "Monatslimit überschritten"
    if daily_used + requested_amount > DAILY_LIMIT:
        return False, "Tageslimit überschritten"
    return True, "OK"
```

### 12.3 Sicherheit
- Niemals echte Bankdaten in Logs
- Alle Passwörter hashen (bcrypt)
- SQL-Injection verhindern (Prepared Statements)
- XSS-Schutz im Frontend

---

## 5. Rechtliche Anforderungen (Frontend/Webseite)

### 5.1 Öffentliche Webseite (Google Sites/Custom)

#### Pflichtseiten (nach CanG und DSGVO)
| Seite | Inhalt | Pflicht |
|-------|--------|---------|
| **Startseite** | Überblick, Werte, Kontakt | ✅ |
| **Mitgliedschaft** | Antragsformular, Preise, FAQ | ✅ |
| **Sorten/Preise** | Aktuelle Sorten, Preisliste | ✅ |
| **Suchtprävention** | Info, Beratungsstellen, Hilfe | ✅ (CanG) |
| **Satzung** | PDF-Download, Änderungshistorie | ✅ |
| **Impressum** | Vereinsdaten, Vorstand, Kontakt | ✅ |
| **Datenschutz** | DSGVO-konforme Erklärung | ✅ |
| **Kontakt** | Formular, Adresse, Öffnungszeiten | Empfohlen |
| **Mitglieder-Login** | Link zum Backend | ✅ |

#### Impressum (Pflichtangaben)
```
Cannabis Social Club [Name] e.V.
[Postfach/Adresse]
[PLZ Ort]

Vertreten durch:
1. Vorsitzende/r: [Name]
2. Vorsitzende/r: [Name]
Schriftführer/in: [Name]

Kontakt:
E-Mail: [info@club.de]
Telefon: [optional]

Registergericht: Amtsgericht [Stadt]
Vereinsregisternummer: [VR XXXXX]
```

#### Datenschutzerklärung (DSGVO-konform)
**Pflichtangaben:**
1. Verantwortlicher (Vorstand)
2. Datenschutzbeauftragter (wenn >10 Mitarbeiter)
3. Erhobene Daten (Name, Adresse, Bankdaten, etc.)
4. Zweck der Verarbeitung
5. Rechtsgrundlage (Art. 6 DSGVO)
6. Speicherdauer (min. 2 Jahre nach Austritt laut CanG)
7. Weitergabe an Behörden (bei Anfrage)
8. Betroffenenrechte (Auskunft, Löschung, etc.)
9. Cookies/Tracking (nur technisch notwendig)
10. Änderungshistorie

#### Suchtpräventions-Seite (CanG-Anforderung)
```
Pflicht-Inhalte:
- Informationen zu Cannabis-Sucht
- Warnsignale für problematischen Konsum
- Kontakt zu Beratungsstellen
- Links zu professioneller Hilfe
- Suchtpräventions-Quiz (optional)
- Kontaktdaten des Club-Präventionsbeauftragten
```

### 5.2 Backend (Admin-Oberfläche)

#### Login-Seite
- Club-Auswahl (bei Multi-Tenant)
- Benutzername/E-Mail
- Passwort
- 2FA-Code (wenn aktiviert)
- "Passwort vergessen"-Funktion
- Link zu öffentlicher Webseite

#### Impressum/DSGVO im Backend
- Footer mit Link zu Impressum
- Datenschutz-Hinweis bei Formularen
- Cookie-Banner (nur technisch notwendig)
- Auskunftsrecht-Button (eigene Daten exportieren)
- Löschungsrecht (Account deaktivieren)

---

## 6. Parametrisierbare Konfiguration

### 6.1 Appscripts → Backend-Parameter

#### Mitgliedschafts-Workflow (konfigurierbar)
```yaml
mitgliedschaft:
  aufnahmegebühr: 20              # EUR
  mindestmitgliedschaft: 3        # Monate
  max_mitglieder: 500             # pro Club
  beitrittsdatum: "erster_tag_folgemonat"
  
  altersprüfung:
    mindestalter: 21              # Jahre
    wohnsitz_deutschland: true
    wohnsitz_dauer: 6             # Monate
    
  nummernvergabe:
    start: 100000
    schema: "sequentiell"
    
  dokumente:
    aufnahmeantrag: true
    sepa_mandat: true
    selbstauskunft: true
    mitgliedsausweis: true
    
  fristen:
    unterlagen_einreichen: 56     # Tage (8 Wochen)
    kündigungsfrist: 2            # Monate
```

#### Limits & Prävention (konfigurierbar)
```yaml
abgabelimits:
  tageslimit: 25                  # Gramm
  monatslimit: 50                 # Gramm
  
prävention:
  warnschwelle: 40                # Gramm/Monat
  beratungspflicht: 45            # Gramm/Monat
  kritisch: 50                    # Gramm/Monat
  
  indikatoren:
    tägliche_bestellungen: 20     # Tage/Monat
    mengenzuwachs: 30             # % zum Vormonat
    nacht_bestellungen: true      # 22:00-06:00
    
  automatische_maßnahmen:
    wöchentlicher_report: true
    email_an_vorstand: true
    suchtberatung_verlinken: true
    
  suchtberatung:
    verlinkung_aktiv: true
    anbieter:
      - name: "Suchtberatung Leipzig"
        telefon: "0341 12345678"
        email: "beratung@example.de"
        website: "https://suchtberatung-leipzig.de"
      - name: "Deutsche Hauptstelle für Suchtfragen"
        telefon: "0221 901901"
        website: "https://dhs.de"
    automatische_meldung: Bei >45g/Monat automatisch Hinweis in App + E-Mail
```

#### Automatisierung (konfigurierbar)
```yaml
automatisierung:
  zeitzone: "Europe/Berlin"       # Kritisch: MEZ nicht UTC für Limit-Reset!
  limit_reset:
    täglich: "00:00"
    monatlich: "1. 00:00"
    
  mitgliederversammlung:
    termine: ["01.01", "01.04", "01.07", "01.10"]
    uhrzeit: "19:00"
    dauer: 2                      # Stunden
    
    einladung:
      delta_t: 14                 # Tage vorher (konfigurierbar: 7-21)
      kanaele: ["email", "sms"]   # Einzeln oder kombiniert
      prioritaet: "hoch"          # E-Mail: wichtig markieren
      
    erinnerung:
      aktiviert: true
      delta_t: 2                  # Tage vorher (zusätzliche Erinnerung)
      kanaele: ["email"]          # Nur E-Mail für Erinnerung
      
    kalender:
      calender_event: true        # iCal-Datei anhängen
      meet_link_generieren: true  # Google Meet/Zoom Link
      ort_angabe: true            # Adresse oder "Online"
      
    teilnehmer:
      nur_aktive_mitglieder: true # Nur akzeptiert + verifiziert
      ausweis_check: true         # Hinweis auf Ausweispflicht
      anmeldePflicht: false       # Freiwillige Teilnahme
    
  inaktivitäts_check:
    tage: 60
    nur_mit_newsletter: true
    
  zahlungserinnerung:
    erste_mahnung: 7              # Tage
    zweite_mahnung: 14            # Tage
    dritte_mahnung: 21            # Tage
    
  dokumente_generierung:
    template_system: "google_docs" # oder "custom"
    platzhalter_format: "{{name}}"
```

#### E-Mail-Kommunikation (konfigurierbar)
```yaml
email:
  absender: "info@csc-leipzig.eu"
  antwort_an: "vorstand@csc-leipzig.eu"
  
  templates:
    mitgliedschaftsantrag:
      betreff: "✨ Ihre Mitgliedschaftsunterlagen"
      anhänge: ["aufnahmeantrag", "sepa", "selbstauskunft", "ausweis"]
      
    mitgliederversammlung:
      betreff: "✨ Mitgliederversammlung am {{datum}}"
      calender_event: true
      meet_link: true
      
    inaktivitäts_erinnerung:
      betreff: "✨ Wir vermissen Ihre Vorbestellungen!"
      sortenliste: true
      
  signatur:
    name: "Cannabis Social Club Leipzig Süd e.V."
    adresse: "Postfach 35 03 04, 04165 Leipzig"
    email: "info@csc-leipzig.eu"
    telefon: "+4917643291439"
```

---

## 7. Erweiterte Features (aus Competitor-Analyse)

### 7.1 Sicherheit & Compliance (Kritisch)

#### Zwei-Faktor-Authentifizierung (2FA)
- **Beschreibung**: Zusätzliche Sicherheitsebene für Admin-Zugriff
- **Methoden**: TOTP (Authenticator-App), SMS-Backup
- **Pflicht für**: System-Admin, Geschäftsführer, Vorstand
- **Optional für**: Kassierer, Mitarbeiter
- **Compliance**: DSGVO-Pflicht bei sensiblen Daten

#### Änderungsprotokoll (Minimal)
- **Erfassung**: Nur wichtige Änderungen (Mitgliedsstatus, Zahlungen, Abgaben)
- **Daten**: Wer, Wann, Was (keine Details zu Lesevorgängen)
- **Speicherung**: 2 Jahre (CanG)
- **Export**: Bei Bedarf für Behörden
- **Kein Audit für**: Profil-Updates, Einstellungen-Änderungen (zu viel Overhead)

#### Session-Management
- **Automatischer Logout**: Nach 30 Minuten Inaktivität
- **Parallele Sessions**: Max. 3 pro Benutzer
- **Session-Überwachung**: Liste aktiver Sessions, Remote-Logout
- **IP-Logging**: Für Sicherheitsprüfungen
- **IP-Whitelisting**: Admin-Zugriff nur von bestimmten IPs (optional)

#### Breach Notification (Datenleck-Meldung) - Automatisiert
- **Pflicht**: DSGVO Art. 33/34 - Meldung innerhalb 72 Stunden
- **Trigger**: Automatisch bei erkanntem Datenleck (ungewöhnliche Zugriffe, Failed Logins >100/h)
- **Workflow**:
  1. System erkennt Anomalie (z.B. Massen-Download, unautorisierter Admin-Zugriff)
  2. Automatische E-Mail an Datenschutzbeauftragten + Vorstand
  3. E-Mail an betroffene Mitglieder (wenn bestätigt)
  4. Meldung an Aufsichtsbehörde (LSI) mit Template
- **Inhalt**: Art des Vorfalls, betroffene Daten, Maßnahmen, Kontakt
- **Protokollierung**: Unveränderbarer Nachweis der Meldung mit Zeitstempel
- **Frist-Tracking**: Countdown 72h sichtbar im Admin-Dashboard

### 7.2 Mitgliederverwaltung (Erweitert)

#### Digitale Mitgliedsausweise
- **Format**: QR-Code + Mitgliedsnummer
- **Anzeige**: Name, Foto, Gültigkeitsdatum
- **Verifikation**: QR-Scan bei Abholung
- **App-Integration**: iOS/Android Wallet
- **Backup**: PDF-Version zum Ausdrucken

#### Doppelmitgliedschaft-Check
- **Datenbank**: Abgleich mit anderen CSCs (wenn API verfügbar)
- **Eidesstattliche Erklärung**: Checkbox im Antrag
- **Stichproben**: Manuelle Prüfung durch Vorstand
- **Sanktion**: Automatische Sperre bei Verstoß

#### Doppelmitgliedschaft-Prüfung (Kritisch!)
- **Eidesstattliche Erklärung**: Checkbox im Antrag (verpflichtend)
- **Datenbank-Abgleich**: Ggf. mit anderen CSCs (API falls verfügbar)
- **Stichproben**: Manuelle Überprüfung durch Vorstand (monatlich)
- **Sanktion**: Automatische Sperre bei Verstoß, Vorstand informieren
- **Dokumentation**: Unterschriften für 2 Jahre aufbewahren (CanG)

#### Kündigungsfrist-Tracking
- **Automatische Berechnung**: 2 Monate zum Quartalsende
- **Erinnerungen**: 30, 14, 7 Tage vor Ablauf
- **Status**: Aktiv → Gekündigt → Ausgetreten
- **Bestätigung**: Automatische Kündigungsbestätigung

#### Verifizierungs-Workflow (Feingranular)
```
DOKUMENTE_EINGEREICHT → IN_PRÜFUNG → VIDEO_CALL_GEPLANT → VERIFIZIERT
      ↓                      ↓              ↓                  ↓
   Antrag               Vorstand        Termin            Aktivierung
   eingegangen          prüft          vereinbart         des Kontos
```
- **Automatische Eskalation**: Erinnerung nach 14 Tagen ohne Fortschritt
- **Video-Call**: Integration Jitsi/Zoom für Altersprüfung
- **Dokumenten-Status**: Einzelne Uploads tracken (Ausweis, Wohnsitznachweis)

### 7.3 Finanzen (Erweitert)

#### SEPA-Workflows (Vollständig)
- **Mandatsverwaltung**:
  - Erstellung mit eindeutiger Mandatsreferenz
  - Widerruf mit Begründung
  - Archivierung (2 Jahre)
  - Status-Tracking (Aktiv/Widerrufen/Ausgelaufen)

- **Batch-Einzüge**:
  - Sammelbuchung aller offenen Posten
  - Vorschau vor Ausführung
  - Einzel- oder Sammelbuchung
  - Status-Tracking (Ausstehend/Eingezogen/Rückläufer)

- **Rückläufer-Handling**:
  - Automatische Erkennung
  - Benachrichtigung an Mitglied + Kassierer
  - Wiedervorlage-Liste
  - Manuelle Nachbuchung

#### Mahnwesen (Automatisiert)
- **Stufen**:
  1. Zahlungserinnerung (7 Tage nach Fälligkeit)
  2. Erste Mahnung (14 Tage, 5€ Mahngebühr)
  3. Zweite Mahnung (21 Tage, 10€ Mahngebühr)
  4. Dritte Mahnung (28 Tage, 15€ Mahngebühr + Sperre)

- **Kanäle**: E-Mail, Post (bei wiederholten Mahnungen)
- **Automatisierung**: Täglicher Cronjob
- **Eskalation**: Automatische Mitgliedschaftssperre

#### DATEV-Export
- **Format**: DATEV-CSV (Standard)
- **Inhalt**: Kontenrahmen, Buchungssätze, Belegnummern
- **Zeitraum**: Monatlich, Quartalsweise, Jährlich
- **Übertragung**: Automatischer Upload (SFTP) oder Download
- **Abstimmung**: Saldi mit Bankkonto

#### Echte vs. Unechte Beiträge (USt-Berechnung)
- **Echte Beiträge**: USt-frei (ideeller Bereich, z.B. Vereinszweck)
- **Unechte Beiträge**: 7% USt (wirtschaftlicher Bereich, z.B. Cannabis-Abgabe)
- **Automatische Berechnung**: Basierend auf Produktkategorie
- **Ausweisung**: Separate Positionen auf Rechnung
- **Prüfung**: Hinweis bei Grenzüberschreitung (>35.000€/Jahr)

#### Spenden-Tracking
- **Separat von Beiträgen**: Steuerlich absetzbar für Spender
- **Spendenbescheinigung**: Automatische Generierung (Jahresende)
- **Sammelspendenbescheinigung**: Bei <300€/Jahr pro Spender
- **Dokumentation**: Zweckbindung der Spenden

#### Bargeld-Abrechnung (Ausgabestellen)
- **Tagesabschluss**: Kassenstand, Ein- und Ausgaben
- **Quittungsnummern**: Lückenlose Nummerierung prüfen
- **Abweichungen**: Differenzen dokumentieren und begründen
- **Einzahlung**: Nachweis Bank/Zentrale

### 7.4 Anbau & Lager (Seed-to-Sale)

#### Neue Django Apps Struktur
```
apps/
├── cultivation/          # Anbaudokumentation
│   ├── models: Mutterpflanze, Steckling, Blütezyklus
│   ├── services: Dünger-Tracking, Pflanzenschutz
│   └── admin: Anbau-Übersicht für Vorstand
│
├── compliance/           # Gesetzeskonformität
│   ├── models: Limit-Register, Verdachtsanzeige, Präventionsprotokoll
│   ├── services: Automatische Sperre, Jahresmeldung
│   └── admin: Compliance-Dashboard
│
└── participation/        # Mitglieds-Mitwirkung
    ├── models: Arbeitsstunden, Schichten, Pflichtstunden
    ├── services: Stunden-Tracking, Schichtplanung
    └── admin: Engagement-Übersicht
```

#### CanG Compliance Features (Kritisch)

**Jugendschutzbeauftragter**
- Benennung im System mit Sachkunde-Nachweis
- Dokumentation der Schulungen
- Jährliche Fortbildungserinnerung

**Präventionskonzept (standortspezifisch)**
- Dokumentation des vom Vorstand erstellten Konzepts
- Pflichtinformationen bei ERSTER Abgabe (Suchtprävention, Wirkungen, Risiken)
- Mitglied bestätigt Kenntnisnahme digital

**Sicherungskonzept**
- Dokumentation: Einbruchschutz, Tresore, Alarmanlage
- Zutrittskontrolle: Wer hat wann Zugang (Protokoll)
- Bestandsschutz: Überwachung gegen Diebstahl

**Konsumverbot Überwachung**
- Protokollierung: Kein Konsum innerhalb 100m des Vereins
- Hinweisschilder dokumentiert
- Mitgliederklärung: Kein Konsum vor Ort

**Beipackzettel (Pflichtangaben)**
- Automatische Generierung mit:
  - Gewicht, Erntedatum, MHD
  - Sortenname, THC/CBD-Gehalt
  - Warnhinweise (Schwangerschaft, Fahren, Mischkonsum)
  - Herkunft (Charge-ID für Rückverfolgung)
- Druck bei jeder Abgabe

**Jahresmeldung an Behörden**
- Automatische Generierung (31.12.)
- Anonymisierte Daten:
  - Gesamterzeugte Menge (g)
  - Lagerstand (g)
  - Abgegebene Mengen pro Mitglied (anonymisiert)
  - Durchschnittlicher THC/CBD-Gehalt
- Export als PDF/CSV
- Erinnerung an Vorstand 30 Tage vor Frist

**Wohnsitzprüfung (>6 Monate)**
- Dokumentation: Meldebescheinigung oder vergleichbarer Nachweis
- Automatische Prüfung: Eintrittsdatum + 6 Monate = Freischaltung
- Erinnerung an Mitglied: Nachweis einreichen

#### Growtagebuch (Detailliert)
- **Räume**: Anbau-, Trocknungs-, Lager-Räume
- **Equipment**: LEDs, Klimaanlagen, Filter, Bewässerung
- **Aktivitäten**:
  - Bewässerung (Menge, pH-Wert, Nährstoffe)
  - Düngung (Produkt, Menge, Datum)
  - Schädlingsbekämpfung
  - Ernte (Datum, Erntemenge, Qualität)

- **Dokumentation**: Fotos optional
- **Export**: PDF für Behörden

#### Pflanzen-Tracking (Einzeln, nicht nur Chargen)
- **Pflanzen-ID**: Eindeutige Nummer pro Pflanze
- **Lebenszyklus**: Steckling → Vegetation → Blüte → Ernte
- **Mutterpflanzen**: Vererbung der ID bei Stecklingen
- **QR-Code**: Physisches Label an der Pflanze
- **Historie**: Vollständige Herkunft einer einzelnen Pflanze

#### Schädlings-Protokoll
- **Befallsbild**: Fotos, betroffene Pflanzen, Ausmaß
- **Maßnahme**: Produkt, Menge, Anwendungsdatum
- **Quarantäne**: Isolierung betroffener Pflanzen
- **Erfolgskontrolle**: Nach 7 Tagen Folgeprüfung
- **Dokumentation**: Für Bio-Zertifizierung relevant

#### Ernte-Prognose
- **Blütezeit**: Automatische Berechnung basierend auf Sorte
- **Erntefenster**: Frühe/optimale/späte Ernte
- **Mengenschätzung**: Basierend auf letztem Gewicht/Stück
- **Verfügbarkeitsanzeige**: "Verfügbar in ca. 3 Wochen"

#### THC/CBD-Erfassung
- **Laborwerte**: Eingabe nach Analyse
- **Produkte**: Verknüpfung mit Chargen
- **Anzeige**: Auf Infozettel und Etiketten
- **Warnungen**: Bei Abweichungen von Sorten-Standard

#### Lager-Bestandsklassen
- **Klassen**: A+ (Premium), A (Standard), B (Geringere Qualität)
- **Zuordnung**: Bei Einlagerung durch Vorstand
- **Preisgestaltung**: Unterschiedliche Preise pro Klasse
- **Berichte**: Übersicht nach Klassen

#### Inventur-Funktion
- **Jährliche Inventur**: Vollständige Zählung
- **Stichproben**: Monatliche Teilinventur
- **Differenzen**: Automatische Abgleichung mit System
- **Bericht**: Inventurbericht für Behörden

#### Abfallnachweise
- **Vernichtung**: Dokumentation vernichteter Chargen
- **Gründe**: MHD überschritten, Qualitätsmangel, Beschlagnahme
- **Zeuge**: Zweiter Vorstand als Zeuge
- **Unterschrift**: Digitale Unterschrift beider Zeugen
- **Archivierung**: Unveränderbare Dokumentation
- **Automatisierung**: Bei Vernichtung automatisch PDF generieren + E-Mail an Vorstand

#### Seed-to-Sale Tracking (Erweitert - CanG-kritisch)
- **Lückenlose Kette**: Steckling-ID → Pflanzen-ID → Charge-ID → Verkauf
- **Herkunftsnachweis**: Woher kam der Steckling (legaler Bezug)
- **Mutterpflanzen-Tracking**: Vererbung der Genetik
- **Zwischenstufen**: Vegetation → Blüte → Ernte → Trocknung → Lagerung
- **Qualitätsstufen**: A+, A, B pro Charge dokumentieren
- **Rückverfolgbarkeit**: Bei Rückruf alle betroffenen Mitglieder identifizieren (innerhalb 24h)

### 7.5 Ausgabe & Distribution (Erweitert)

#### Transportbescheinigungen
- **Automatische Generierung**: Bei Ausgabe
- **Inhalt**: Menge, Sorte, THC/CBD, Ausgabedatum, Mitgliederdaten
- **Format**: PDF mit QR-Code
- **Rechtsgrundlage**: CanG Übergabedokumentation
- **Archivierung**: 2 Jahre

#### Reservierungssystem
- **Vorauswahl**: Mitglieder reservieren online
- **Zeitfenster**: Abholung innerhalb 48h
- **Timeout**: Automatische Freigabe nach 48h (kritisch: blockiert sonst Bestand)
- **Streichung**: Automatisch nach Ablauf
- **Benachrichtigung**: Erinnerung vor Ablauf (24h + 2h vorher)
- **Priorisierung**: Nach Wartezeit/Fairness

#### Warteliste (bei Ausverkauf)
- **FIFO**: First In, First Out (gerecht)
- **Priorität**: Optional: Langjährige Mitglieder bevorzugt
- **Benachrichtigung**: Automatisch wenn Sorte verfügbar
- **Zeitfenster**: 24h zur Reservierung nach Freigabe

#### Express-Abholung (Zeitfenster-Buchung)
- **Terminwahl**: 15-Minuten-Fenster (z.B. 18:00-18:15)
- **Wartezeit**: Reduzierung durch exakte Planung
- **Pünktlichkeit**: Verspätung = Verfall der Reservierung (15 Min.)
- **Reservierung**: Nur mit aktivem Guthaben möglich

#### Bevollmächtigung (Delegierung)
- **Vollmacht**: Digitale Erteilung im Mitgliederbereich
- **Bevollmächtigter**: Name, Geburtsdatum, Ausweisnummer
- **Ausweiskopie**: Upload bei Erteilung der Vollmacht
- **Limit-Prüfung**: Trotzdem gegen Mitgliedslimits
- **Protokollierung**: Wer hat für wen abgeholt

### 7.6 Mobile App (Mitglieder)

#### Kernfunktionen
- **Digitale Ausweise**: QR-Code für schnelle Identifikation
- **Bestellung**: Mobile Sortenauswahl und Reservierung
- **Kontostand**: Guthaben und offene Posten
- **Historie**: Vergangene Bestellungen und Limits
- **Push-Benachrichtigungen**: Neue Sorten, Erinnerungen

#### Technische Anforderungen
- **Plattformen**: iOS 14+, Android 10+
- **Offline-Modus**: Grundfunktionen ohne Internet
- **Sicherheit**: Biometrische Authentifizierung
- **Updates**: Automatisch über App-Stores

#### Offline-Bestellung
- **Warteschlange**: Bestellungen werden lokal gespeichert
- **Synchronisierung**: Automatisch bei Verbindung
- **Konfliktlösung**: Warnung wenn Sorte zwischenzeitlich ausverkauft
- **Queue-Status**: Anzeige "Wartet auf Übermittlung"

#### Dark Mode
- **Diskrete Nutzung**: Weniger auffällig in der Öffentlichkeit
- **Akku-Schonung**: OLED-Displays profitieren
- **Automatik**: Je nach System-Einstellung

#### Schneller Checkout (Biometrie)
- **Face-ID/Fingerprint**: Ein-Klick-Bestellung
- **Express-Abholung**: Schnellerer Zugang
- **Sicherheit**: Biometrie nur für Bestätigung, nicht für Login

### 7.7 API & Integrationen

#### SMS-Gateway (für Mitgliederversammlung & Alerts)
- **Anbieter**: Twilio, MessageBird, or SMS77
- **Versand**: Automatisch bei wichtigen Ereignissen
- **Kosten**: ~0,05-0,10€ pro SMS
- **Inhalte**:
  - Mitgliederversammlungseinladung (kurz)
  - Erinnerung (1 Tag vorher)
  - Wichtige Club-Infos (Notfälle, Ausfälle)
- **Opt-In**: Mitglied muss SMS explizit erlauben (DSGVO)
- **Abmelden**: "STOP" Funktion

#### REST API
- **Authentifizierung**: OAuth 2.0 / API-Keys
- **Ratenlimit**: 1000 Requests/Stunde
- **Dokumentation**: OpenAPI/Swagger
- **Versionierung**: v1, v2, etc.

#### Schnittstellen
- **Steuerberater-Software**: DATEV, Addison
- **Banking**: FinTS/HBCI für Kontenabruf
- **E-Mail**: SMTP für Versand
- **SMS**: Gateway für 2FA und Benachrichtigungen
- **Kalender**: iCal-Export für Termine

### 7.8 Community-Features (Optional)

#### Interne Kommunikation
- **Forum**: Themenbasierte Diskussionen
- **Chat**: Direktnachrichten zwischen Mitgliedern
- **Events**: Veranstaltungskalender intern
- **Dokumente**: Mitgliederbereich mit Downloads

#### Social Features
- **Profile**: Optionale öffentliche Profile
- **Freundschaften**: Vernetzung zwischen Mitgliedern
- **Gruppen**: Interessengruppen bilden

### 7.10 Dashboard & Widgets

#### Tages-Übersicht (Startseite)
- **Neue Mitglieder**: Anzahl heute/letzte 7 Tage
- **Ausgaben**: Heutige Abgaben, Umsatz
- **Warnungen**: Farblich hervorgehoben
  - Niedriger Bestand (< 10% Mindestbestand)
  - Offene Zahlungen (> 7 Tage überfällig)
  - Unvollständige Verifizierungen (> 14 Tage)
  - Anstehende Mitgliederversammlungen

#### Schnell-Links
- Häufige Aktionen: "Neues Mitglied", "Bestellung erfassen", "Ausgabe buchen"
- Letzte Aktionen: Wiederholen-Funktion

#### Statistik-Widgets
- Mitglieder-Wachstum (Diagramm)
- Top-Sorten (Meistbestellte Sorten)
- Finanz-Übersicht (Umsatz Monat/Quartal)

### 7.11 Admin-Panel Einstellungen (Konfigurationsoberfläche)

#### Mitgliederversammlung Einstellungen
**Pfad**: Admin → Einstellungen → Mitgliederversammlung

```yaml
einstellungen_mitgliederversammlung:
  termine:
    quartal_1: "01.01"
    quartal_2: "01.04"
    quartal_3: "01.07"
    quartal_4: "01.10"
    uhrzeit: "19:00"
    dauer: 2
    
  einladung:
    delta_t:                      # Slider: 7-21 Tage
      wert: 14
      min: 7
      max: 21
      schritt: 1
    kanaele:                      # Checkboxen
      email: true
      sms: true
    prioritaet: "hoch"            # Dropdown: normal/hoch/wichtig
    
  erinnerung:
    aktiviert: true               # Toggle
    delta_t: 2                    # Slider: 1-7 Tage
    kanaele:
      email: true
      sms: false
      
  kalender:
    calender_event_anhaengen: true
    meet_link_generieren: true
    ort: "Online (Google Meet)"   # Textfeld
    
  teilnehmer:
    nur_aktive_mitglieder: true
    ausweis_check_hinweis: true
    max_teilnehmer: 500           # Number input
```

**UI-Komponenten**:
- **Slider** für Delta-T (visuell: 7-21 Tage)
- **Toggle-Switches** für Aktivierung/Deaktivierung
- **Checkboxen** für Kanäle (E-Mail, SMS)
- **Dropdown** für E-Mail-Priorität
- **Vorschau**: Nächste Versandtermine automatisch berechnen
- **Test-Modus**: Einladung an Test-E-Mail/SMS senden

**Berechtigungen**:
- Nur Geschäftsführer und Vorstand können ändern
- Änderungen werden im Audit-Trail protokolliert
- Bei Änderung: Bestätigungsdialog mit Hinweis auf betroffene Mitglieder

#### Multi-Language Support
- **Sprachen**: Deutsch, Englisch (weitere optional)
- **Mitglieder-Präferenz**: Individuell wählbar
- **Automatische Erkennung**: Browser-Sprache als Default
- **Rechtliche Texte**: Immer Deutsch (maßgeblich)

#### Rollen-Vorlagen
- **Schnellzuweisung**: "Standard-Mitarbeiter", "Vorstand", "Kassierer"
- **Berechtigungs-Pakete**: Vordefinierte Kombinationen
- **Individuelle Anpassung**: Nach Zuweisung modifizierbar
- **Neue Vorlagen**: Selbst erstellbar

#### Daten-Retention (Automatische Löschung)
- **Aufbewahrungsfristen**: 2 Jahre nach Austritt (CanG)
- **Anonymisierung**: Nach Frist personenbezogene Daten entfernen
- **Archiv**: Nur statistische Daten behalten
- **DSGVO-konform**: Recht auf Vergessen automatisiert
- **Ausnahme**: Finanzdaten 10 Jahre (Steuerrecht)

#### Automatisierung Übersicht (Dashboard)
**Pfad**: Admin → Dashboard → Automatisierung

```yaml
automation_dashboard:
  naechste_ereignisse:
    - ereignis: "Mitgliederversammlung Q1"
      datum: "01.01.2027"
      einladung_versand: "18.12.2026"      # Automatisch berechnet (delta_t)
      erinnerung_versand: "30.12.2026"      # Automatisch berechnet
      status: "Geplant"
      
  aktive_cronjobs:
    - name: "Täglicher Limit-Reset"
      zeit: "00:00"
      status: "Aktiv"
      letzte_ausfuehrung: "Heute 00:00"
      
    - name: "Monatlicher Limit-Reset"
      zeit: "1. 00:00"
      status: "Aktiv"
      naechste_ausfuehrung: "01.04.2027"
      
    - name: "Mitgliederversammlungseinladung"
      trigger: "Täglich (Prüfung Delta-T)"
      status: "Aktiv"
      naechster_versand: "18.12.2026"
```

### 7.12 Kritische Fallstricke & Warnungen

#### Rechtliche Fallstricke
1. **Delta-T zu kurz** (<7 Tage)
   - **Problem**: Rechtlich problematisch, Mitglieder können klagen
   - **Lösung**: Minimum 7 Tage, empfohlen 14 Tage
   - **Validierung**: System blockiert Werte <7

2. **SMS ohne Opt-in**
   - **Problem**: DSGVO-Verstoß, Bußgelder bis 20 Mio. € oder 4% Umsatz
   - **Lösung**: Explizite Einwilligung erforderlich, Double-Opt-In
   - **Dokumentation**: Einwilligung mit Zeitstempel speichern

3. **Audit-Trail löschbar**
   - **Problem**: Manipulation möglich, Vertrauensverlust
   - **Lösung**: Append-only Datenbank, kryptografische Prüfsummen
   - **Backup**: Unveränderbare externe Kopie

4. **THC-Werte falsch**
   - **Problem**: Strafrechtliche Konsequenzen, Behördenmaßnahmen
   - **Lösung**: Labortests dokumentieren, Toleranzbereiche definieren
   - **Haftung**: Keine Garantie übernehmen, nur dokumentieren

5. **Limit-Reset Zeitzone**
   - **Problem**: Server in USA = Reset um 18:00 MEZ
   - **Lösung**: Explizit Europe/Berlin Zeitzone
   - **DST**: Sommer-/Winterzeit automatisch beachten

#### Technische Fallstricke
6. **Doppelte Mitgliedsnummern**
   - **Problem**: Race Condition bei gleichzeitiger Registrierung
   - **Lösung**: Datenbank-Constraint (UNIQUE), Transaktionen

7. **Gleichzeitige Bestellungen**
   - **Problem**: Bestand überschritten bei parallelen Sessions
   - **Lösung**: Pessimistisches Locking, Bestandsreservierung

8. **SEPA-Rückläufer nach Mahnung**
   - **Problem**: Mitglied bereits gemahnt, aber Zahlung doch eingegangen
   - **Lösung**: Idempotente Verarbeitung, Status-Checks

9. **Backup während Abgabe**
   - **Problem**: Inkonsistente Daten (Bestand bereits reduziert, Log noch nicht)
   - **Lösung**: Transaktionen, Point-in-Time Recovery

#### Organisatorische Fallstricke
10. **Fehlende Schulung**
    - **Problem**: Mitarbeiter wissen nicht, wie System funktioniert
    - **Lösung**: Pflichtschulung, Handbuch, Videos

11. **Kein Notfallplan**
    - **Problem**: Systemausfall bei Abgabetag
    - **Lösung**: Papier-Backup-Prozess, manuelle Quittungen

12. **Datenexport vergessen**
    - **Problem**: Beim Wechsel zu anderer Software keine Migration
    - **Lösung**: Monatliche Exporte, standardisierte Formate

---

## Anhang A: Legacy Appscripts (Referenz)

Die folgenden Google Appscripts wurden aus dem alten System extrahiert und dienen als Referenz für die Implementierung:

### A.1 FormSubmit.gs
**Funktion**: Verarbeitung neuer Mitgliedschaftsanträge
- Trigger: Bei Formular-Submit
- Aktionen:
  - Duplikat-Prüfung (E-Mail)
  - Altersprüfung (21+)
  - Mitgliedsnummer-Vergabe (fortlaufend ab 100000)
  - Beitrittsdatum = 1. Folgemonat
  - Telefonnummer-Normalisierung (+ → 00)
  - Status-Initialisierung (Akzeptiert/Verifiziert/Zahlung = Nein)
  - Zeilen-Farbmarkierung (#B7CDE8)
  - E-Mail-Versand mit Dokumenten

### A.2 RestLimitDay.gs
**Funktion**: Tägliches Zurücksetzen der Tageslimits
- Trigger: Täglich (00:00 Uhr)
- Aktion: Tagesabgabe aller Mitglieder auf 25g setzen

### A.3 RestLimitMonth.gs
**Funktion**: Monatliches Zurücksetzen der Monatslimits
- Trigger: Täglich (prüft ob 1. des Monats)
- Aktion: Monatsabgabe aller Mitglieder auf 50g setzen (nur am 1.)

### A.4 NotifyOrder.gs
**Funktion**: Benachrichtigung bei Inaktivität
- Trigger: Täglich
- Bedingung: 60 Tage ohne Bestellung + akzeptiert + verifiziert + Newsletter
- Aktion: E-Mail mit Sortenangebot und Bestelllink

### A.5 MembershipInvitation.gs (Neu: Konfigurierbar)
**Funktion**: Automatische Einladung zu Mitgliederversammlungen
- Trigger: Täglich (prüft auf konfigurierbares Delta-T vor Quartalsbeginn)
- Termine: 01.01., 01.04., 01.07., 01.10. (konfigurierbar)
- Delta-T: Konfigurierbar (7-21 Tage vorher, Standard: 14 Tage)
- Kanäle: E-Mail + optional SMS
- Features:
  - Google Calendar Event mit Meet-Link (iCal-Anhang)
  - E-Mail an alle akzeptierten Mitglieder (hohe Priorität)
  - SMS-Benachrichtigung (optional, Opt-in erforderlich)
  - Zusätzliche Erinnerung 2 Tage vorher
  - Template-System für personalisierte Einladungen
  - Vorschau im Admin-Panel (nächste geplante Versände)

### A.6 SendMembershipDocuments.gs
**Funktion**: Versand personalisierter Dokumente
- Trigger: Bei Antragseingang (gleicher Tag)
- Dokumente: Aufnahmeantrag, SEPA-Mandat, Selbstauskunft, Mitgliederausweis
- Technik: Google Docs Template → PDF → E-Mail-Anhang

## Anhang B: Formular-Strukturen

### B.1 Mitgliedschaftsantrag (Google Form)
**Pflichtfelder:**
- E-Mail-Adresse
- Vorname, Nachname
- Geburtsdatum
- Straße, Hausnummer
- Postleitzahl, Stadt
- Telefonnummer
- Datenschutzerklärung (Checkbox)
- IBAN, BIC, Kreditinstitut
- SEPA-Lastschriftmandat (Checkbox)
- Keine andere CSC-Mitgliedschaft (Checkbox)
- Fester Wohnsitz in Deutschland (Checkbox)
- Mindestalter 21 Jahre (Checkbox)
- Aktueller Lichtbildausweis (Checkbox)
- Newsletter wichtige Ankündigungen (Checkbox)
- Optionaler Newsletter (Checkbox)

### B.2 Bestellformular (Google Form)
**Struktur:**
- Mitgliedsnummer (Validierung)
- Zeitstempel (automatisch)
- Auswahl der Sorten (8 Blüten + 8 Stecklinge)
- Mengenfelder (in Gramm)
- Hinweis: Automatische Limit-Prüfung

---

**Letzte Aktualisierung**: 2025-03-01  
**Autor**: Biodanza / OpenClaw  
**Status**: Requirements Phase