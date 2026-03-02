# CSC Administration - 10-Phasen Roadmap

## Phase 0: Setup (Woche 1-2)
- Django-Projekt, PostgreSQL, Tailwind, Docker
- Tests: DB-Verbindung, Tailwind lädt

## Phase 1: Core (Woche 3-5)
- Authentifizierung, Rollen (Mitglied/Vorstand), Admin-Panel
- Tests: Login/Logout, Rollen-Zuweisung

## Phase 2: Mitgliedschaft (Woche 6-8)
- Registrierung (21+), Verifizierung, Mitgliedsnummern, 8-Wochen-Deadline
- Tests: Altersprüfung, Akzeptanz-Workflow, E-Mail-Versand

## Phase 3: MVP Launch (Woche 9-12) 🚀
- Shop, Warenkorb, Limit-Prüfung (25g/50g), Guthaben-Zahlung, Reservierung
- Tests: Limit-Durchsetzung, Happy Path Kauf, Reservierung-Timeout

## Phase 4: Compliance (Woche 13-15)
- CanG-Reports, Verdachtsanzeige, Jahresmeldung, Prävention
- Tests: >50g erzeugt Alert, Jahresmeldung-Export

## Phase 5: Finanzen (Woche 16-18)
- SEPA-Mandate, Lastschrift, Mahnwesen (4 Stufen), DATEV-Export
- Tests: SEPA-Einzug, Mahn-Eskalation, DATEV-Format

## Phase 6: Inventar (Woche 19-21)
- cultivation App, Seed-to-Sale, Chargen, Vernichtungsnachweise
- Tests: Rückverfolgbarkeit, Vernichtungsprotokoll

## Phase 7: Automatisierung (Woche 22-23)
- participation App, Cronjobs (Limit-Reset, Einladungen), Workflows
- Tests: Daily Reset, Meeting-Einladungen, Inaktivitäts-Benachrichtigung

## Phase 8: Mobile & UX (Woche 24-26)
- PWA, Dark Mode, WCAG-Barrierefreiheit (50+), Touch-Optimierung
- Tests: PWA-Install, Kontrast-Check, Touch-Targets

## Phase 9: Polish (Woche 27-28)
- Performance (Query-Optimierung, Caching), Dokumentation, Bugfixing
- Tests: Ladezeit <2s, N+1 Query-Check

**Gesamt: 28 Wochen (7 Monate)**
**Keine KI-Funktionalität** ✅
