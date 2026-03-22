# Seed Data

Dieses Verzeichnis enthaelt die Demo-/QA-Daten fuer die CSC-Administration.

Ziele:
- reproduzierbare Datensaetze fuer Docker-Bootstrap und Playwright-Screenshots
- realistische Pseudodaten mit Varianz bei Rollen, Status, Guthaben, Rechnungen und Bestellungen
- idempotentes Reseeding ohne Duplikate

Dateien:
- `users.json`: Nutzer, Profile, Karten, Engagement und SEPA-Stammdaten
- `catalog.json`: Sorten, Lagerorte, Inventar, Batches, Grow Cycles und Harvest-Batches
- `activity.json`: Bestellungen, Rechnungen, Shifts, Messaging-, Compliance- und Governance-Daten

Der Import erfolgt ueber:

```bash
python src/manage.py seed_demo_data --reset
```
