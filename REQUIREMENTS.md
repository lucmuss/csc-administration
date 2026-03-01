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
- **Verifikations-Workflow**: Altersprüfung (21+), Wohnsitzverifizierung, Ausschluss anderer CSCs
- **Status-Tracking**: Antrag → Akzeptiert → Verifiziert → Aktiv
- **Abgabelimits**: 50g/Monat, 25g/Tag (gesetzlich vorgeschrieben)
- **Guthaben-Verwaltung**: Kontostand für Vorauszahlungen

### 2.2 Bestellsystem
- **Sorten-Auswahl**: Blüten und Stecklinge mit Live-Bestand
- **Warenkorb**: Automatische Limit-Prüfung (Monats- und Tageslimits)
- **Zahlung**: Bar, Überweisung oder Lastschrift (SEPA)
- **Ausgabe-Planung**: Monatliche Verteilungstermine

### 2.3 Inventar & Abgabe
- **Chargen-Tracking**: Herkunft, Erntedatum, Qualitätsgrade
- **Abgabe-Logging**: Zeitstempel, Menge, verbleibende Limits
- **Compliance-Reports**: Nachweis für Behörden

### 2.4 Finanzen
- **Zahlungs-Tracking**: Offene Posten, eingegangene Zahlungen
- **SEPA-Lastschrift**: Mandatsverwaltung, automatische Abbuchung
- **Buchhaltung**: Export für Steuerberater

### 2.5 Automatisierung & Workflows (aus Appscripts)

#### Mitgliedschafts-Workflow
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

---

## 3. Datenmodell

### 3.1 Entitäten

```
Member (Mitglied)
├── Personal: name, birth_date, address, contact
├── Membership: number, join_date, status, limits
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
- Trennt Bankdaten (DSGVO)
- Erkennt Duplikate

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

---

## 6. Rechtliche Anforderungen

### 6.1 CanG (Cannabisgesetz)
- Abgabe nur an Mitglieder ab 21 Jahren
- Max. 50g/Monat, 25g/Tag pro Mitglied
- Keine Weitergabe an Dritte
- Dokumentationspflicht (2 Jahre)

### 6.2 DSGVO
- Einwilligung nachweisbar speichern
- Zweckbindung der Daten
- Löschung nach Austritt (nach Aufbewahrungsfrist)
- Auskunftsrecht für Mitglieder

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

### A.5 MembershipInvitation.gs
**Funktion**: Einladung zu Mitgliederversammlungen
- Trigger: Täglich (prüft auf 6 Tage vor Quartalsbeginn)
- Termine: 01.01., 01.04., 01.07., 01.10.
- Features:
  - Google Calendar Event mit Meet-Link
  - E-Mail an alle akzeptierten Mitglieder
  - Template-System für personalisierte Einladungen

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