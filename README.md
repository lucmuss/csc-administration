# CSC Admin System

> Cannabis Social Club Verwaltungssystem  
> Mitgliederverwaltung, Bestellsystem, Abgabe-Tracking

---

## 📁 Projekt-Struktur

```
projects/csc-app/
├── cdata/                          # Daten-Templates (JSON)
│   ├── member_template.json        # Beispiel-Mitglieder
│   ├── strains.json                # Verfügbare Sorten
│   ├── order_template.json         # Beispiel-Bestellungen
│   └── README.md                   # Daten-Dokumentation
├── database_schema.sql             # SQL-Schema (SQLite)
├── import_members.py               # Import-Skript (Excel → DB)
├── REQUIREMENTS.md                 # System-Anforderungen
└── README.md                       # Diese Datei
```

---

## 🚀 Schnellstart

### 1. Mitglieder aus Excel importieren

```bash
python3 import_members.py import mitglieder.xlsx
```

Mit eigener Datenbank:
```bash
python3 import_members.py import mitglieder.xlsx mein_club.db
```

### 2. Daten als CSV exportieren

```bash
python3 import_members.py export mein_club.db backup.csv
```

---

## 📋 Excel-Import-Format

Die Excel-Datei muss folgende Spalten enthalten:

| Spalte | Pflicht | Beschreibung |
|--------|---------|--------------|
| E-Mail-Adresse | ✅ | Mitglieds-E-Mail |
| Vorname | ✅ | Vorname |
| Nachname | ✅ | Nachname |
| Geburtsdatum | ✅ | Excel-Datum |
| Mitgliedsnummer | ✅ | z.B. 100004 |
| Straße, Hausnummer | | Adresse |
| Postleitzahl | | PLZ |
| Stadt | | Stadt |
| Telefonnummer | | Telefon |
| Aufnahmedatum | | Excel-Datum |
| Beitrittsdatum | | Excel-Datum |
| IBAN | | Bankverbindung |
| BIC | | BIC-Code |
| Kreditinstitut | | Bank-Name |
| Monatsabgabe | | Limit in Gramm (default: 50) |
| Tagesabgabe | | Limit in Gramm (default: 25) |
| Guthaben | | Kontostand |
| Datenschutzerklärung | | Ja/Nein |
| Ermächtigung zur Lastschrift | | Ja/Nein |
| Mindestalter 21 Jahre | | Ja/Nein |
| Fester Wohnsitz in Deutschland | | Ja/Nein |
| Mitgliedschaft anderer Anbaugemeinschaften | | Ja/Nein |
| Aktueller Lichtbildausweis | | Ja/Nein |
| Newsletter für wichtige Ankündigungen | | Ja/Nein |
| Optionaler Newsletter | | Ja/Nein |
| Akzeptiert | | Ja/Nein |
| Verifiziert | | Ja/Nein |
| Zahlung | | Ja/Nein |

---

## 🗄️ Datenbank-Schema

### Tabellen

- **members** – Mitglieder (Basisdaten)
- **member_bank_details** – Bankdaten (DSGVO-separat)
- **strains** – Verfügbare Sorten
- **orders** – Bestellungen
- **order_items** – Bestellpositionen
- **distribution_log** – Abgabe-Log (Compliance)
- **inventory** – Lagerbestand
- **audit_log** – Änderungshistorie

Siehe `database_schema.sql` für vollständiges Schema.

---

## 📊 cdata/ – Daten-Templates

Das `cdata/`-Verzeichnis enthält anonymisierte Beispiel-Daten:

| Datei | Inhalt |
|-------|--------|
| `member_template.json` | Beispiel-Mitglieder mit vollständiger Struktur |
| `strains.json` | Alle 16 Sorten (8 Blüten + 8 Stecklinge) |
| `order_template.json` | Beispiel-Bestellungen |

**Verwendung:**
- Als Template für Import-Skripte
- Testdaten für Entwicklung
- Referenz für API-Datenstruktur

---

## 🔒 Sicherheit & DSGVO

### Datenschutz-Features

✅ **Getrennte Speicherung:**
- Bankdaten in eigener Tabelle
- Verschlüsselung möglich

✅ **Consent-Tracking:**
- Datenschutz-Einwilligung
- SEPA-Mandat
- Newsletter-Opt-ins

✅ **Audit-Log:**
- Alle Änderungen protokolliert
- Nachvollziehbarkeit

### Verschlüsselung (optional)

```python
# SQLCipher für SQLite
from pysqlcipher3 import dbapi2 as sqlite3

conn = sqlite3.connect('csc_database.db')
conn.execute("PRAGMA key = 'mein-sicherer-schluessel'")
```

---

## ⚖️ Rechtliche Hinweise

### CanG (Cannabisgesetz)
- Abgabe nur an Mitglieder ab 21 Jahren
- Max. 50g/Monat, 25g/Tag
- Dokumentationspflicht (2 Jahre)

### DSGVO
- Einwilligung nachweisbar speichern
- Recht auf Löschung
- Datenportabilität

---

## 🛠️ Entwicklung

### Abhängigkeiten

Nur Python 3 Standard-Bibliothek – keine Installation nötig!

Optional:
```bash
pip install pysqlcipher3  # Verschlüsselung
pip install pandas        # Alternative Excel-Verarbeitung
```

### Datenbank-Abfragen

```bash
sqlite3 csc_database.db

# Beispiele:
SELECT COUNT(*) FROM members;
SELECT * FROM members WHERE status = 'active';
SELECT * FROM member_bank_details WHERE member_id = 1;
```

---

## 📚 Weitere Dokumentation

- **[REQUIREMENTS.md](REQUIREMENTS.md)** – Detaillierte System-Anforderungen
- **[cdata/README.md](cdata/README.md)** – Daten-Format-Spezifikationen

---

## 📝 Lizenz & Hinweis

Dies ist ein Template/Beispiel-System für CSC-Verwaltung. Für produktiven Einsatz:
- Sicherheitsaudit durchführen
- Rechtliche Beratung einholen
- Datenschutz-Folgenabschätzung erstellen

**Niemals echte Mitgliederdaten in Repositorys oder unverschlüsselt speichern!**

---

**Letzte Aktualisierung**: 2025-03-01

---

## 🧪 Test-Eintrag

Hallo, wie geht's? Dies ist ein Test-Commit vom nanobot Assistant! 🐈