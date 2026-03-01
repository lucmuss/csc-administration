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

**Letzte Aktualisierung**: 2025-03-01  
**Autor**: Biodanza / OpenClaw  
**Status**: Requirements Phase