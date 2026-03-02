# CSC Administration - Implementierungs-Aufgabe

## Ziel
Django-Verwaltungssystem für Cannabis Social Club (CSC) nach deutschem CanG.

## Stack
- Django 5 + Python 3.11
- PostgreSQL (Docker)
- Tailwind CSS + Alpine.js
- PyTest

## Phase 1: Setup (Stunde 1)
1. Django-Projektstruktur erstellen (src/, apps/, templates/, static/)
2. pyproject.toml mit uv
3. Docker Compose (PostgreSQL, Django)
4. Tailwind CSS Setup
5. Basis-Template (base.html)

## Phase 2: Core (Stunde 2)
1. Custom User Model (E-Mail statt Username)
2. Accounts-App mit Login/Logout
3. Rollen: Mitglied, Mitarbeiter, Vorstand
4. Admin-Dashboard (Custom, nicht Django-Admin)

## Phase 3: Mitgliedschaft (Stunde 3-4)
1. Members-App
2. Registrierung mit Altersprüfung (21+)
3. Mitgliedsnummern (ab 100000)
4. Verifizierungs-Workflow
5. Profil-Verwaltung

## Phase 4: MVP Shop (Stunde 5-8) - WICHTIGSTE
1. Orders-App
2. Inventory-App
3. Sorten-Verwaltung
4. Warenkorb
5. KRITISCH: Limit-Prüfung (25g/Tag, 50g/Monat)
6. Guthaben-System
7. Reservierung (48h)

## Phase 5: Compliance (Stunde 9-10)
1. CanG-Berichte
2. Limit-Reset (täglich/monatlich)
3. Verdachtsanzeige bei >50g
4. Tests mit PyTest

## Datenmodelle
- User: email, first_name, last_name, is_staff
- Profile: member_number, status, balance, daily_used, monthly_used
- Strain: name, thc, cbd, price, stock
- Order: member, items, total, status

## Tests
- PyTest für alle kritischen Features
- Mindestens: Login, Limit-Prüfung, Bestellung

## NICHT implementieren
- KI-Funktionalität
- Mobile App
- Multi-Tenant
- Komplexe Reports

Starte mit Phase 1.
