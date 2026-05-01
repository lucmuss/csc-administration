# Seed Data

Dieses Verzeichnis enthaelt die Demo-/QA-Daten fuer die CSC-Administration.

Ziele:
- reproduzierbare Datensaetze fuer Docker-Bootstrap und Playwright-Screenshots
- realistische Pseudodaten mit Varianz bei Rollen, Status, Guthaben, Rechnungen und Bestellungen
- idempotentes Reseeding ohne Duplikate

Dateien:
- `social_clubs.json`: Social Clubs (inkl. Regionen/Bundeslaender) und Oeffnungszeiten
- `users.json`: Nutzer, Profile, Karten, Engagement und SEPA-Stammdaten
- `catalog.json`: Sorten, Lagerorte, Inventar und Beispiel-Chargen
- `activity.json`: Beispiel-Bestellungen, Rechnungen, Zahlungen, Inventur und Schichten
- `governance.json`: Vorstandssitzungen, Agenda, Beschluesse und Aufgaben
- `messaging.json`: E-Mail-Gruppen, Mitgliedszuordnungen und Vorlagen

Der Import erfolgt ueber:

```bash
python src/manage.py seed_demo_data --reset
```

Automatischer Start-Import:

```bash
AUTO_SEED_DEMO_DATA=1 bash scripts/start-web.sh
```
