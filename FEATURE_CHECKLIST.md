# CSC Administration - Feature-Checkliste & Validierung

> Alle Features aus REQUIREMENTS.md und Competitor-Analysen
> Validierungs-Status: Implementiert? Getestet?

---

## 📊 Validierungs-Übersicht

| Kategorie | Features | Validated | Status |
|-----------|----------|-----------|--------|
| 1. Setup & Core | 8 | ⏳ | - |
| 2. Mitgliedschaft | 12 | ⏳ | - |
| 3. Bestellung & Limits | 15 | ⏳ | - |
| 4. Inventar & Anbau | 14 | ⏳ | - |
| 5. Finanzen | 12 | ⏳ | - |
| 6. Compliance | 10 | ⏳ | - |
| 7. Automatisierung | 8 | ⏳ | - |
| 8. Mobile & UX | 6 | ⏳ | - |
| **GESAMT** | **85** | **0/85** | **0%** |

---

## 1. SETUP & CORE (8 Features)

### 1.1 Django-Projektstruktur
- [ ] Django 5 + Python 3.11 Setup
- [ ] PostgreSQL-Datenbank
- [ ] Docker + docker-compose
- [ ] uv Package Manager
- [ ] pyproject.toml (wie RedFlag Analyzer)

### 1.2 Frontend-Stack
- [ ] Tailwind CSS Integration
- [ ] Alpine.js für Interaktivität
- [ ] HTMX für Server-Side Rendering
- [ ] Basis-Template (base.html)

### 1.3 Core-Features
- [ ] Custom User Model (E-Mail statt Username)
- [ ] Login/Logout/Passwort-Reset
- [ ] Rollen-System (Mitglied, Mitarbeiter, Vorstand)
- [ ] Admin-Dashboard (Custom, nicht Django-Admin)

---

## 2. MITGLIEDSCHAFT (12 Features)

### 2.1 Registrierung
- [ ] Registrierungsformular
- [ ] Altersprüfung (21+)
- [ ] Wohnsitz-Validierung (>6 Monate)
- [ ] E-Mail-Verifizierung (Double-Opt-In)

### 2.2 Mitgliedsverwaltung
- [ ] Mitgliedsnummern-Vergabe (ab 100000)
- [ ] Status-Workflow (pending → verified → active)
- [ ] Dokumenten-Upload (Ausweis, Wohnsitznachweis)
- [ ] 8-Wochen-Deadline-Tracking

### 2.3 Verifizierung
- [ ] Admin-Übersicht ausstehende Anträge
- [ ] Akzeptieren/Ablehnen mit Begründung
- [ ] Automatische E-Mail bei Status-Änderung
- [ ] Profil anzeigen/bearbeiten

---

## 3. BESTELLUNG & LIMITS (15 Features)

### 3.1 Shop
- [ ] Sorten-Verwaltung (Name, THC, CBD, Preis)
- [ ] Shop-Übersicht (Blüten, Stecklinge)
- [ ] Produktdetails
- [ ] Warenkorb (Session-basiert)

### 3.2 Limits (KRITISCH)
- [ ] Tageslimit 25g - Prüfung in Echtzeit
- [ ] Monatslimit 50g - Prüfung in Echtzeit
- [ ] Automatische Blockierung bei Überschreitung
- [ ] Reset um 00:00 Uhr (täglich)
- [ ] Reset am 1. des Monats (monatlich)

### 3.3 Bestellprozess
- [ ] Checkout mit Guthaben-Prüfung
- [ ] 48h-Reservierung
- [ ] Timeout-Automatik (nach 48h)
- [ ] Quittungsdruck/-PDF
- [ ] Bestellhistorie

### 3.4 Zahlung
- [ ] Guthaben-System (Aufladen, Abbuchen)
- [ ] Manuelle Zahlungserfassung (Bar, Überweisung)
- [ ] Zahlungsstatus-Tracking

---

## 4. INVENTAR & ANBAU (14 Features)

### 4.1 Inventar-Basis
- [ ] Chargen-Tracking (Charge-ID, MHD, THC/CBD)
- [ ] Lager-Bestandsklassen (A+, A, B)
- [ ] Lagerort-Verwaltung
- [ ] Inventur-Funktion

### 4.2 Seed-to-Sale
- [ ] Steckling-Tracking (Herkunft)
- [ ] Pflanzen-Tracking (Lebenszyklus)
- [ ] Ernte-Dokumentation
- [ ] Chargen-Rückverfolgbarkeit

### 4.3 Anbau (cultivation App)
- [ ] Mutterpflanzen-Verwaltung
- [ ] Growtagebuch (Bewässerung, Düngung)
- [ ] Dünger/Pflanzenschutz-Log
- [ ] Ernte-Prognose

### 4.4 Qualität & Vernichtung
- [ ] THC/CBD-Erfassung pro Charge
- [ ] Abfallnachweise (Vernichtung)
- [ ] Vernichtungsprotokoll (2 Zeugen)
- [ ] Rückruf-System (24h Identifikation)

---

## 5. FINANZEN (12 Features)

### 5.1 SEPA
- [ ] SEPA-Mandatsverwaltung
- [ ] Mandatsreferenz-Generierung
- [ ] SEPA-Lastschrift (Batch-Einzug)
- [ ] Vorabankündigung per E-Mail (1 Tag)
- [ ] Rückläufer-Handling

### 5.2 Mahnwesen
- [ ] Stufe 1: Erinnerung (7 Tage)
- [ ] Stufe 2: 1. Mahnung + 5€ (14 Tage)
- [ ] Stufe 3: 2. Mahnung + 10€ (21 Tage)
- [ ] Stufe 4: 3. Mahnung + 15€ + Sperre (28 Tage)

### 5.3 Buchhaltung
- [ ] DATEV-Export (CSV)
- [ ] USt-Split (7% Cannabis / 19% Merchandise)
- [ ] Kassenbuch (GoBD-konform)
- [ ] Rechnungswesen
- [ ] Finanz-Berichte

---

## 6. COMPLIANCE (10 Features)

### 6.1 CanG-Compliance
- [ ] Verdachtsanzeige (>50g/Monat, automatisch)
- [ ] Jahresmeldung an Behörden (anonymisiert)
- [ ] Bestandsmeldung
- [ ] Jugendschutzbeauftragter-Verwaltung

### 6.2 Prävention
- [ ] Präventionskonzept-Dokumentation
- [ ] Info-Pflicht bei erster Abgabe
- [ ] Suchtberatung-Verlinkung
- [ ] Verbrauchswarnungen (40g/45g/50g)

### 6.3 Sicherheit
- [ ] Sicherungskonzept-Dokumentation
- [ ] Zutrittskontrolle-Protokollierung

---

## 7. AUTOMATISIERUNG (8 Features)

### 7.1 Cronjobs
- [ ] Täglicher Limit-Reset (00:00)
- [ ] Monatlicher Limit-Reset (1. des Monats)
- [ ] Reservierungs-Timeout (48h)
- [ ] Zahlungserinnerungen

### 7.2 Benachrichtigungen
- [ ] Inaktivitäts-Benachrichtigung (60 Tage)
- [ ] Mitgliederversammlung-Einladung (14 Tage vorher)
- [ ] Mitgliederversammlung-Erinnerung (2 Tage vorher)
- [ ] 8-Wochen-Deadline-Erinnerung

---

## 8. MOBILE & UX (6 Features)

### 8.1 PWA
- [ ] manifest.json
- [ ] Service Worker
- [ ] Offline-Fähigkeit (Basis)

### 8.2 Barrierefreiheit
- [ ] Touch-Optimierung (44x44px Buttons)
- [ ] Hohe Kontraste (WCAG AA)
- [ ] Klare visuelle Feedback-Meldungen

---

## ✅ VALIDIERUNGS-PROTOKOLL

### Batch 1: Core-Features (3/85)

#### Feature 1.1: Custom User Model (E-Mail)
- **Geprüft:** `src/apps/accounts/models.py`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `class User(AbstractBaseUser): email = models.EmailField(unique=True)`
- **Tests:** `tests/test_auth.py` - ✅ VORHANDEN

#### Feature 1.2: Login/Logout
- **Geprüft:** `src/apps/accounts/views.py`, `templates/accounts/login.html`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `def login_view(request)`, Template mit Form
- **Tests:** `tests/test_auth.py::test_login_success` - ✅ VORHANDEN

#### Feature 1.3: Rollen-System
- **Geprüft:** `src/apps/accounts/models.py`, `src/config/settings.py`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** Django Groups verwendet, `@login_required`, `@permission_required`
- **Tests:** `tests/test_auth.py` - ✅ VORHANDEN

**Ergebnis Batch 1: 3/3 Features validiert ✅**

---

### Batch 2: Mitgliedschaft (3/85)

#### Feature 2.1: Registrierungsformular
- **Geprüft:** `src/apps/members/views.py`, `templates/members/register.html`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `def register(request)` mit Formular
- **Tests:** - ⚠️ KEINE SPEZIFISCHEN TESTS GEFUNDEN

#### Feature 2.2: Altersprüfung (21+)
- **Geprüft:** `src/apps/members/forms.py`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `clean_birth_date()` mit `calculate_age() >= 21`
- **Tests:** - ⚠️ KEINE SPEZIFISCHEN TESTS GEFUNDEN

#### Feature 2.3: Mitgliedsnummern (ab 100000)
- **Geprüft:** `src/apps/members/models.py`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `member_number = models.CharField()`, `generate_member_number()`
- **Tests:** - ⚠️ KEINE SPEZIFISCHEN TESTS GEFUNDEN

**Ergebnis Batch 2: 3/3 Features validiert (Tests fehlen teilweise) ⚠️**

---

### Batch 3: Bestellung & Limits (3/85)

#### Feature 3.1: Warenkorb (Session)
- **Geprüft:** `src/apps/orders/views.py`, `templates/orders/cart.html`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `CART_SESSION_KEY`, `_load_cart()`, `_save_cart()`
- **Tests:** `tests/test_orders.py` - ✅ VORHANDEN

#### Feature 3.2: Tageslimit 25g (KRITISCH)
- **Geprüft:** `src/apps/orders/services.py`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `check_limits()`, `daily_used + quantity > 25`
- **Tests:** `tests/test_limits.py::test_daily_limit_enforced` - ✅ VORHANDEN

#### Feature 3.3: Monatslimit 50g (KRITISCH)
- **Geprüft:** `src/apps/orders/services.py`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `monthly_used + quantity > 50`
- **Tests:** `tests/test_limits.py::test_monthly_limit_enforced` - ✅ VORHANDEN

**Ergebnis Batch 3: 3/3 Features validiert ✅**

---

### Batch 4: Inventar (3/85)

#### Feature 4.1: Chargen-Tracking
- **Geprüft:** `src/apps/inventory/models.py`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `class Strain`, `class Batch` mit `batch_number`, `harvest_date`
- **Tests:** - ⚠️ KEINE TESTS GEFUNDEN

#### Feature 4.2: Sorten-Verwaltung
- **Geprüft:** `src/apps/inventory/views.py`, `templates/inventory/strain_list.html`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `StrainListView`, Template mit Liste
- **Tests:** - ⚠️ KEINE TESTS GEFUNDEN

#### Feature 4.3: cultivation App
- **Geprüft:** `src/apps/cultivation/`
- **Status:** ❌ NICHT IMPLEMENTIERT
- **Beweis:** Verzeichnis nicht vorhanden
- **Tests:** ❌ KEINE

**Ergebnis Batch 4: 2/3 Features validiert (cultivation fehlt) ⚠️**

---

### Batch 5: Finanzen (3/85)

#### Feature 5.1: SEPA-Mandatsverwaltung
- **Geprüft:** `src/apps/finance/models.py`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `class SepaMandate` mit `mandate_reference`, `iban`, `bic`
- **Tests:** `tests/test_finance.py` - ✅ VORHANDEN

#### Feature 5.2: SEPA-Lastschrift
- **Geprüft:** `src/apps/finance/management/commands/collect_sepa_payments.py`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** Management Command für Batch-Einzug
- **Tests:** `tests/test_finance.py` - ✅ VORHANDEN

#### Feature 5.3: 4-Stufen-Mahnwesen
- **Geprüft:** `src/apps/finance/services.py`, `management/commands/send_reminders.py`
- **Status:** ✅ IMPLEMENTIERT
- **Beweis:** `ReminderService` mit `LEVEL_1`, `LEVEL_2`, `LEVEL_3`, `LEVEL_4`
- **Tests:** `tests/test_finance.py::test_reminder_escalation` - ✅ VORHANDEN

**Ergebnis Batch 5: 3/3 Features validiert ✅**

---

## 📊 ZWISCHENSTAND

**Validiert: 15/85 Features (17%)**

| Kategorie | Validated | Status |
|-----------|-----------|--------|
| Setup & Core | 3/8 | ✅ Gut |
| Mitgliedschaft | 3/12 | ⚠️ Tests fehlen |
| Bestellung & Limits | 3/15 | ✅ Gut |
| Inventar | 2/14 | ⚠️ cultivation fehlt |
| Finanzen | 3/12 | ✅ Gut |
| Compliance | 0/10 | ⏳ Nicht geprüft |
| Automatisierung | 0/8 | ⏳ Nicht geprüft |
| Mobile & UX | 0/6 | ⏳ Nicht geprüft |

**Nächste Validierung:** Batch 6-8 (Compliance, Automatisierung, Mobile)

Soll ich die Validierung fortsetzen?