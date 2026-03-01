# CSC Data Directory (cdata/)

Dieses Verzeichnis enthält Beispiel-Daten und Templates für das CSC Admin System.

## 📁 Dateien

### `member_template.json`
Beispiel-Mitglieder (anonymisiert) mit vollständiger Datenstruktur.

**Enthält:**
- Persönliche Daten (Name, Adresse, Kontakt)
- Mitgliedschaftsdetails (Nummer, Status, Limits)
- Consent/DSGVO-Informationen
- Bankdaten (IBAN, BIC, SEPA-Mandat)

**Verwendung:**
- Template für Import-Skripte
- Testdaten für Entwicklung
- Referenz für Datenstruktur

### `strains.json`
Verfügbare Cannabis-Sorten (Blüten und Stecklinge).

**Enthält:**
- 8 Blüten-Sorten (7-9€/g)
- 8 Steckling-Sorten (5€/g)
- Preise, Verfügbarkeit, Kategorie

**Struktur:**
```json
{
  "id": 1,
  "name": "Orange Bud",
  "type": "flower|clone",
  "category": "bluete|steckling",
  "price_per_gram": 8.0,
  "availability": 0,
  "is_active": true
}
```

### `order_template.json`
Beispiel-Bestellungen mit Positionen.

**Enthält:**
- Bestellkopf (Mitglied, Datum, Status)
- Bestellpositionen (Sorten, Mengen, Preise)
- Zahlungsinformationen

## 🔒 Datenschutz

**Wichtig:** Alle Daten in diesem Verzeichnis sind:
- Anonymisiert (keine echten Personendaten)
- Als Template gedacht
- Für Entwicklung und Testzwecke

**Niemals echte Mitgliederdaten hier speichern!**

## 🛠️ Verwendung

### Import in Datenbank
```bash
# Mitglieder importieren
python3 ../import_members.py import mitglieder.xlsx

# Sorten importieren (eigener Befehl nötig)
python3 import_strains.py strains.json
```

### Als Referenz
Die JSON-Dateien zeigen die erwartete Datenstruktur für:
- API-Endpoints
- Datenbank-Schema
- Import-Formate

## 📝 Format-Spezifikationen

### Datum
- ISO 8601 Format: `YYYY-MM-DD` oder `YYYY-MM-DDTHH:MM:SSZ`

### Preise
- Dezimalzahl mit Punkt: `8.50`
- Währung: Euro (€)

### Mengen
- In Gramm (g)
- Ganzzahlen für Abgabelimits

### Booleans
- JSON native: `true` / `false`
- Nicht: "Ja"/"Nein" oder 1/0

## 🔄 Aktualisierung

Bei Änderungen am Datenmodell:
1. Diese Templates aktualisieren
2. Import-Skripte anpassen
3. Datenbank-Schema migrieren

## 📚 Siehe auch

- `../REQUIREMENTS.md` – System-Anforderungen
- `../database_schema.sql` – SQL-Schema
- `../import_members.py` – Import-Skript