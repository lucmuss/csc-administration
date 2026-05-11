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

## Forgejo AI Workflow

Dieses Repo kann auf Forgejo ueber einen self-hosted Runner automatisiert Issues durch KI bearbeiten.

Vorgesehener Ablauf:

- Forgejo-Issue anlegen
- Label `ai:ready` setzen
- Der Runner startet den Codex-Workflow
- Die KI erstellt einen Branch `ai/issue-<nummer>`, implementiert die Aenderung, prueft lokale Checks, erstellt PR und merged bei Erfolg

Aktuell als Merge-Gate genutzt:

- `./.venv/bin/python src/manage.py check`
- `./.venv/bin/pytest tests/test_auth.py tests/test_finance.py tests/test_mobile.py tests/test_orders.py tests/test_limits.py tests/test_automation.py tests/test_inventory_advanced.py -q`

Noch nicht Teil des automatischen Merge-Gates:

- Cultivation/Legacy Seed-to-Sale Bereiche mit bestehender Test- und Modell-Divergenz
- einzelne Compliance-/Alt-Tests, die noch nicht auf den aktuellen Datenmodellstand angepasst sind

## Demo Seed Data

Fuer lokale Umgebungen und Docker-Starts gibt es reproduzierbare Seed-Daten im Repo:

```bash
python src/manage.py seed_demo_data
python src/manage.py seed_demo_data --reset
```

Wenn `AUTO_SEED_DEMO_DATA=1` gesetzt ist, fuehrt `scripts/start-web.sh` den Import beim Start automatisch aus. Die Seed-Daten sind idempotent und aktualisieren bestehende Demo-Eintraege statt sie zu duplizieren.

## PostgreSQL statt SQLite

Die App ist standardmaessig auf PostgreSQL ausgelegt. Fuer lokale Migration von bestehender `db.sqlite3`:

```bash
docker compose up -d db
./scripts/migrate_sqlite_to_postgres.sh
```

Hinweise:

- `docker-compose.yml` startet eine eigene PostgreSQL-Instanz (`db`) mit Volume `postgres_data`.
- Host-Port ist per Default `5434` (konfigurierbar ueber `POSTGRES_HOST_PORT`).
- Datenbank-Umgebungsvariablen koennen als `DATABASE_*`, `DB_*`, `POSTGRES_*` oder `DATABASE_URL` gesetzt werden.

## E-Mail-Testing mit Mailpit

Fuer verifizierbare Agenten- und E2E-Tests (Registrierung, Verifizierungscode, Passwort-Reset):

1. In `.env` Mailpit aktivieren:

```env
EMAIL_DELIVERY_MODE=mailpit
EMAIL_HOST=mailpit
EMAIL_PORT=1025
EMAIL_USE_TLS=0
EMAIL_USE_SSL=0
MAILPIT_HTTP_URL=http://localhost:8025
MAILPIT_API_URL=http://localhost:8025/api/v1
```

2. Dienste starten:

```bash
docker compose up -d db mailpit web
```

3. Inbox pruefen:

- UI: `http://localhost:8025`
- API: `http://localhost:8025/api/v1/messages`

4. Agenten-Helfer nutzen:

```bash
python scripts/mailpit_api.py list
python scripts/mailpit_api.py wait-code --recipient user@example.com --subject-contains Verifizierung
```

Optional:

- `MAILPIT_UI_ENABLED=1` blendet fuer Vorstand/Mitarbeiter in der Navigation unter `Verwaltung` einen Direktlink auf die Mailpit-Oberflaeche ein.

---

## Aktuelle Aenderungen (2026-05-11)

- Finance Archiv:
  - Loeschen-Button direkt in der Tabellenzeile mit sofortigem Redirect/Refresh.
  - Tabellenzeilen farblich markiert: `Bezahlt` leicht gruen, `Offen` leicht gelb.
  - Upload akzeptiert zusaetzliche Dateiformate (`BMP`, `GIF`, `TIFF`, `HEIC`, `AVIF`, `CSV`, `MD`).
  - Upload-Feld `Notizen` entfernt.
  - Status-Auswahl auf `Offen` und `Bezahlt` reduziert.
- Governance:
  - Dashboard-Kachel `Ausweise / Bald ablaufend` entfernt.
  - Aufgabenboard als eigener Punkt unter `Verwaltung` in der Navigation.
  - Task-Status `Blockiert` entfernt (nur `Offen`, `In Arbeit`, `Erledigt`).
  - Voreinstellung `Faellig am` auf `heute + 7 Tage`.
  - Kompaktere Task-Karten mit aufklappbaren Details und Overflow-Fixes.
- Compliance:
  - CSV-Export im Jahresbericht entfernt (Button + Serverausgabe).
- Messaging:
  - Live-Markdown-Vorschau beim Erstellen von Massen-E-Mails.
  - Variablen werden mit aktuellem Benutzerkontext gerendert (`first_name`, `last_name`, `email`, `member_number`).
- Inventory / Shop / Participation / PDF:
  - Abweichungsbericht-Feature entfernt (`/inventory/discrepancies/` inkl. Navigation).
  - Edibles-Kategorie aus Shop-/Inventar-UI und Kern-Filterpfaden entfernt.
  - Inventar-Ansichten (`Sorten`, `Inventur`, `Dashboard`) auf aktiven Social Club begrenzt.
  - Cannabinoid-Felder (`THC/CBD/CBG/CBN/CBC/CBV`) vereinheitlicht, jeweils max. `30%`.
  - Teilnahme-Stundenliste farblich codiert wie Bestellstatus (gruen/gelb).
  - PDF-Rechnung: Abschnitt `Leistungsumfang` mit zusaetzlichem vertikalem Abstand.
- Cultivation:
  - Dashboard ergaenzt um Uebersicht der aktuell angebauten Sorten.
  - Pflanzenerfassung/-bearbeitung verwendet aktive, clubbezogene Shop-Sorten (Blueten/Stecklinge).

---

**Letzte Aktualisierung**: 2026-05-11

---

## 🧪 Test-Eintrag

Hallo, wie geht's? Dies ist ein Test-Commit vom nanobot Assistant! 🐈
