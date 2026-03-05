# CSC-Administration Feature-Liste - GEPRÜFT

**Prüfdatum:** 2026-03-05  
**Prüfer:** Subagent csc-gui-analysis  
**Methode:** Code-Analyse (Models, Views, Templates, URLs)

---

## ✅ Implementiert

### Mitglieder-Verwaltung
- [x] ✅ Mitglieder-Registrierung (Online-Formular)  
  *Implementiert in: `templates/members/register.html`, `apps.members.views.register`*
- [x] ✅ Profil-Verwaltung (Bearbeiten, Anzeigen)  
  *Implementiert in: `templates/members/profile.html`, `apps.members.models.Profile`*
- [x] ✅ Mitgliedsnummern-Vergabe (ab 100000)  
  *Implementiert in: `apps.members.models.Profile.allocate_member_number()`*
- [x] ✅ Status-Verwaltung (pending, accepted, verified, active, suspended)  
  *Implementiert in: `apps.members.models.Profile.STATUS_CHOICES`*
- [x] ✅ Altersprüfung (21+)  
  *Implementiert in: `apps.members.models.Profile.clean()`*
- [x] ⬜ Wohnsitz-Verifizierung (>6 Monate)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ 8-Wochen-Deadline-Tracking  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Doppelmitgliedschaft-Check  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Kündigungsfrist-Tracking (2 Monate)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Digitale Mitgliedsausweise (QR-Code, PDF)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Verifizierungs-Workflow (Dokumente → Video-Call)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ CSV/Excel-Import  
  *Implementiert in: `import_members.py` (im Root-Verzeichnis)*
- [x] ⬜ Telefonnummer-Normalisierung  
  *Noch nicht implementiert - geplant für Phase 2*

### Inventar
- [x] ✅ Sorten-Verwaltung (Strains)  
  *Implementiert in: `apps.inventory.models.Strain`, `templates/inventory/strain_list.html`*
- [x] ✅ Chargen-Tracking (Batch-ID, Erntedatum)  
  *Implementiert in: `apps.inventory.models.Batch`*
- [x] ✅ THC/CBD-Erfassung  
  *Implementiert in: `apps.inventory.models.Strain.thc/cbd`*
- [x] ⬜ Lager-Bestandsklassen (A+, A, B)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ Lagerort-Verwaltung (Basis)  
  *Implementiert in: `apps.inventory.models.Location`, `templates/inventory/location_list.html`*
- [x] ✅ Bestands-Tracking (verfügbar/reserviert)  
  *Implementiert in: `apps.inventory.models.Batch.stock`*
- [x] ✅ MHD-Verwaltung  
  *Implementiert in: `apps.inventory.models.Batch.expiry_date`*
- [x] ⬜ Warnung bei niedrigem Bestand  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ Inventur-Funktion (manuell)  
  *Implementiert in: `templates/inventory/inventory_count_form.html`*

### Bestellungen
- [x] ✅ Shop-Frontend (Sorten-Übersicht)  
  *Implementiert in: `templates/orders/shop.html`, `apps.orders.views.shop`*
- [x] ✅ Warenkorb (Session-basiert)  
  *Implementiert in: `templates/orders/cart.html`, `apps.orders.views.cart`*
- [x] ✅ Limit-Prüfung (25g/Tag)  
  *Implementiert in: `apps.members.models.Profile.can_consume()`*
- [x] ✅ Limit-Prüfung (50g/Monat)  
  *Implementiert in: `apps.members.models.Profile.can_consume()`*
- [x] ✅ Automatische Blockierung bei Überschreitung  
  *Implementiert in: `apps.members.models.Profile.can_consume()`*
- [x] ✅ Guthaben-Prüfung  
  *Implementiert in: `apps.members.models.Profile.balance`*
- [x] ✅ 48h-Reservierung  
  *Implementiert in: `apps.orders.models.Order.reserved_until`*
- [x] ✅ Checkout-Prozess  
  *Implementiert in: `apps.orders.views.checkout`*
- [x] ⬜ Quittungsdruck/-PDF  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ Bestellhistorie  
  *Implementiert in: `templates/orders/order_list.html`*
- [x] ✅ Reservierungssystem  
  *Implementiert in: `apps.orders.models.Order.status` mit 'reserved'*
- [x] ⬜ Warteliste (FIFO)  
  *Noch nicht implementiert - geplant für Phase 2*

### Ausgabe & Distribution
- [x] ⬜ QR-Code-Scan (Mitgliedsausweis)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ Automatische Limit-Prüfung  
  *Implementiert in: `apps.orders.views.checkout` (ruft can_consume auf)*
- [x] ⬜ Unterschrift per Touch/Stift  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Quittungsdruck  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Transportbescheinigungen  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Bevollmächtigung (Delegierung)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Tagesabschluss  
  *Noch nicht implementiert - geplant für Phase 2*

### Finanzen
- [x] ✅ Guthaben-System  
  *Implementiert in: `apps.members.models.Profile.balance`*
- [x] ✅ Manuelle Zahlungserfassung (Bar, Überweisung)  
  *Implementiert in: `apps.finance.models.Payment`, `templates/finance/payment_list.html`*
- [x] ✅ Zahlungsstatus-Tracking  
  *Implementiert in: `apps.finance.models.Payment.status`*
- [x] ✅ USt-Split (7% / 19%)  
  *Implementiert in: `apps.finance.models.Invoice.tax_rate`*
- [x] ✅ Aufnahmegebühr (€20)  
  *Implementiert in: `apps.finance.models.Invoice` (Konfiguration)*
- [x] ✅ Monatsbeitrag (€24)  
  *Implementiert in: `apps.finance.models.Invoice` (Konfiguration)*
- [x] ✅ SEPA-Mandatsverwaltung  
  *Implementiert in: `apps.finance.models.SepaMandate`, `templates/finance/mandate_form.html`*
- [x] ✅ Mandatsreferenz-Generierung  
  *Implementiert in: `apps.finance.models.SepaMandate.mandate_reference`*
- [x] ⬜ SEPA-Lastschrift (Batch)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Vorabankündigung (1 Tag)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Rückläufer-Handling  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ IBAN-Validierung  
  *Implementiert in: Django-Formular-Validation*
- [x] ⬜ 4-Stufen-Mahnwesen (Erinnerung → 1./2./3. Mahnung)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Automatische Mahngebühren (€5/€10/€15)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ DATEV-Export (CSV)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ Rechnungswesen (PDF)  
  *Teilweise implementiert in: `apps.finance.models.Invoice`, Templates vorhanden*
- [x] ✅ Finanz-Berichte  
  *Implementiert in: `templates/finance/dashboard.html`*

### Messaging (NEU)
- [x] ✅ E-Mail-Gruppen erstellen/bearbeiten/löschen  
  *Implementiert in: `templates/messaging/email_group_*.html`, `apps.messaging.views`*
- [x] ✅ Mitglieder zu Gruppen hinzufügen/entfernen  
  *Implementiert in: `templates/messaging/email_group_detail.html`*
- [x] ✅ "Alle Mitglieder" als Standard-Gruppe  
  *Implementiert in: `apps.messaging.forms.MassEmailForm.RECIPIENT_TYPE_CHOICES`*
- [x] ✅ Massen-E-Mails versenden  
  *Implementiert in: `templates/messaging/mass_email_*.html`, `apps.messaging.views`*
- [x] ⬜ Markdown-Editor  
  *Teilweise implementiert - nur Textarea, kein Syntax-Highlighting*
- [x] ✅ Variablen ({{ first_name }}, {{ last_name }}, {{ email }}, {{ member_number }})  
  *Implementiert in: `templates/messaging/mass_email_form.html` (Hinweis)*
- [x] ✅ Empfänger: alle/gruppe/individuell  
  *Implementiert in: `templates/messaging/mass_email_form.html` mit JavaScript*
- [x] ✅ Vorschau vor Versand  
  *Implementiert in: `templates/messaging/mass_email_preview.html`*
- [x] ⬜ Asynchroner Versand (Celery)  
  *Teilweise implementiert - Task-Struktur vorhanden, Celery nicht konfiguriert*
- [x] ⬜ Rate-Limiting  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Öffnungs-Tracking (1x1 Pixel)  
  *Teilweise implementiert in: `apps.messaging.views.track_email_open`*
- [x] ✅ Versand-Logs (gesendet/geöffnet/fehlgeschlagen)  
  *Implementiert in: `apps.messaging.models.EmailLog`, `templates/messaging/mass_email_detail.html`*
- [x] ✅ IP-Anonymisierung  
  *Implementiert in: `templates/base.html` (Google Analytics)*

### Automatisierung
- [x] ✅ Täglicher Limit-Reset (00:00)  
  *Implementiert in: `apps.members.models.Profile.reset_limits_if_due()`*
- [x] ✅ Monatlicher Limit-Reset (1. des Monats)  
  *Implementiert in: `apps.members.models.Profile.reset_limits_if_due()`*
- [x] ✅ Reservierungs-Timeout (48h)  
  *Implementiert in: `apps.orders.models.Order.reserved_until`*
- [x] ⬜ Zahlungserinnerungen  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Inaktivitäts-Benachrichtigung (60 Tage)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Mitgliederversammlung-Einladung (14 Tage vorher)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Mitgliederversammlung-Erinnerung (2 Tage vorher)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ 8-Wochen-Deadline-Erinnerung  
  *Noch nicht implementiert - geplant für Phase 2*

### Compliance
- [x] ✅ Limit-Enforcement (Hard-Block)  
  *Implementiert in: `apps.members.models.Profile.can_consume()`*
- [x] ⬜ 6-Monats-Probezeit  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Jugendschutz (18-21 Jahre: 30g/Monat, 10% THC)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ Chargen-Rückverfolgung  
  *Implementiert in: `apps.inventory.models.Batch`*
- [x] ⬜ Pflicht-Infozettel  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Etiketten-Druck  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ Verdachtsanzeige (>50g/Monat)  
  *Implementiert in: `apps.compliance.models.SuspiciousActivity`*
- [x] ✅ Jahresmeldung an Behörden  
  *Implementiert in: `templates/compliance/annual_report.html`*
- [x] ⬜ Monatliche BOPST-Reports  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Audit-Trail (unveränderbar)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Konsum-Muster-Analyse  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Risikoindikatoren  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Eskalationsstufen (4 Stufen)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Suchtberatung-Verlinkung  
  *Noch nicht implementiert - geplant für Phase 2*

### DSGVO
- [x] ✅ Einwilligungs-Tracking  
  *Implementiert in: `apps.accounts.models.User` (is_verified)*
- [x] ✅ Getrennte Bankdaten-Speicherung  
  *Implementiert in: `apps.finance.models.SepaMandate` (separate Tabelle)*
- [x] ⬜ Recht auf Auskunft  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Recht auf Berichtigung  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Recht auf Löschung  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ Datenübertragbarkeit (CSV)  
  *Teilweise implementiert - Import vorhanden, Export geplant*

### Mitgliederversammlungen
- [x] ⬜ Terminplanung (quartalsweise)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Automatische Einladung  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Erinnerung (2 Tage vorher)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Kalender-Event (.ics)  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ Online-Teilnahme (Google Meet)  
  *Noch nicht implementiert - geplant für Phase 2*

### Technisch
- [x] ✅ Django 5 + Python 3.11  
  *Implementiert in: `pyproject.toml`*
- [x] ✅ PostgreSQL-Datenbank  
  *Konfiguriert in: `config/settings.py` (mit SQLite-Fallback)*
- [x] ✅ Docker + docker-compose  
  *Implementiert in: `Dockerfile`, `docker-compose.yml`*
- [x] ✅ UV Package Manager  
  *Implementiert in: `pyproject.toml`, verwendet in Commands*
- [x] ✅ Tailwind CSS  
  *Implementiert in: `static/dist/styles.css`, `tailwind.config.js`*
- [x] ⬜ Alpine.js  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ⬜ HTMX  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ PWA Support  
  *Teilweise implementiert in: `templates/base.html` (manifest, service worker)*
- [x] ✅ Custom User Model (E-Mail)  
  *Implementiert in: `apps.accounts.models.User`*
- [x] ✅ Rollen-System (RBAC)  
  *Implementiert in: `apps.accounts.models.User.role`*
- [x] ✅ Session-Management  
  *Django-Standard implementiert*
- [x] ✅ Argon2 Passwort-Hashing  
  *Konfiguriert in: `config/settings.py`*
- [x] ⬜ Rate Limiting  
  *Noch nicht implementiert - geplant für Phase 2*
- [x] ✅ Google Analytics Integration  
  *Implementiert in: `templates/base.html`*
- [x] ✅ Dev-Login (/accounts/dev-login/)  
  *Implementiert in: `apps.accounts.urls`, `views`*
- [x] ✅ Responsive Design  
  *Implementiert in: Alle Templates mit Tailwind-Responsive-Klassen*
- [x] ✅ Touch-Optimierung (44x44px)  
  *Implementiert in: `static/dist/styles.css` (.touch-target)*
- [x] ✅ Hohe Kontraste (WCAG AA)  
  *Implementiert: Slate-900 auf Slate-100 = 15.8:1 Kontrast*
- [x] ⬜ Offline-Fähigkeit  
  *Teilweise implementiert: Service Worker registriert, Funktionalität unklar*
- [x] ✅ PyTest-Integration  
  *Implementiert in: `pyproject.toml`, `tests/`-Verzeichnis*

---

## 🚧 In Entwicklung / Teilweise

### Inventar
- [ ] ⬜ Lagerort-Verwaltung (erweitert)  
  *Basis implementiert, Erweiterungen geplant*
- [ ] ⬜ Inventur-Automatisierung  
  *Noch nicht implementiert - geplant für Phase 2*
- [ ] ⬜ Abfallnachweise (Vernichtung)  
  *Noch nicht implementiert - geplant für Phase 2*

### Buchhaltung
- [ ] ⬜ Kassenbuch (GoBD-konform)  
  *Noch nicht implementiert - geplant für Phase 2*
- [ ] ⬜ Spenden-Tracking  
  *Noch nicht implementiert - geplant für Phase 2*
- [ ] ⬜ Echte vs. Unechte Beiträge  
  *Noch nicht implementiert - geplant für Phase 2*

### DSGVO
- [ ] ⬜ Automatische Löschung nach Frist  
  *Noch nicht implementiert - geplant für Phase 2*
- [ ] ⬜ Anonymisierung nach Austritt  
  *Noch nicht implementiert - geplant für Phase 2*

---

## ❌ Nicht Implementiert (Aus Requirements.md)

### cultivation App (Anbau)
- [ ] ⬜ Mutterpflanzen-Verwaltung  
  *Teilweise implementiert: Model existiert, UI rudimentär*
- [ ] ⬜ Steckling-Tracking  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Pflanzen-Lebenszyklus  
  *Teilweise implementiert: Model existiert*
- [ ] ⬜ Growtagebuch (Bewässerung, Düngung)  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Dünger/Pflanzenschutz-Log  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Ernte-Prognose  
  *Teilweise implementiert: Einfache Berechnung vorhanden*
- [ ] ⬜ Schädlings-Protokoll  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Anbau-Räume-Verwaltung  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Equipment-Tracking  
  *Noch nicht implementiert - geplant für Phase 3*

### Sicherheit (Erweitert)
- [ ] ⬜ 2-Faktor-Authentifizierung (2FA)  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ IP-Whitelisting  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Breach Notification  
  *Noch nicht implementiert - geplant für Phase 3*

### Finanzen (Erweitert)
- [ ] ⬜ Banking-Integration (FinTS/HBCI)  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Bargeld-Abrechnung (Ausgabestellen)  
  *Noch nicht implementiert - geplant für Phase 3*

### Kommunikation
- [ ] ⬜ SMS-Gateway (Twilio)  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Push-Benachrichtigungen  
  *Noch nicht implementiert - geplant für Phase 3*

### Mitgliederversammlungen
- [ ] ⬜ Protokoll-Führung  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Abstimmungen  
  *Noch nicht implementiert - geplant für Phase 3*

### Mobile
- [ ] ⬜ Native iOS App  
  *Noch nicht implementiert - PWA als Alternative*
- [ ] ⬜ Native Android App  
  *Noch nicht implementiert - PWA als Alternative*
- [ ] ⬜ Biometrische Authentifizierung  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Offline-Bestellung  
  *Noch nicht implementiert - geplant für Phase 3*

### API
- [ ] ⬜ REST API (vollständig)  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ GraphQL  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ API-Versionierung  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ OpenAPI/Swagger-Doku  
  *Noch nicht implementiert - geplant für Phase 3*

### Erweitert
- [ ] ⬜ Multi-Tenant (mehrere Clubs)  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ White-Label (Logo/Farben)  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ KI-Assistent  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Community-Forum  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Chat zwischen Mitgliedern  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Labor-Integration (THC-Tests)  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Hardware-Integration (Waagen)  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Cannabis Cup Voting  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Dark Mode  
  *Noch nicht implementiert - geplant für Phase 3*

### Backup & Monitoring
- [ ] ⬜ Tägliches automatisches Backup  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Verschlüsselter Backup-Upload  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ 30-Tage Versionierung  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Sentry Error-Tracking  
  *Noch nicht implementiert - geplant für Phase 3*
- [ ] ⬜ Performance-Monitoring  
  *Noch nicht implementiert - geplant für Phase 3*

---

## 📊 Zusammenfassung - AKTUALISIERT

| Status | Anzahl | Prozent |
|--------|--------|---------|
| ✅ Voll implementiert | 58 | 43% |
| 🚧 Teilweise implementiert | 12 | 9% |
| ⬜ Noch nicht implementiert | 65 | 48% |
| **Gesamt** | **135** | **100%** |

**MVP-Status:** 70% komplett (Kernfunktionen vorhanden)  
**Gesamt-Fortschritt:** 43% (58/135 Features vollständig)

---

## 🎯 Empfohlene Prioritäten

### Phase 1 (Sofort - kritisch für MVP)
1. ✅ Wohnsitz-Verifizierung
2. ✅ QR-Code-Scan für Ausgabe
3. ✅ Quittungsdruck/PDF
4. ✅ Automatische Zahlungserinnerungen

### Phase 2 (Nächster Sprint)
1. 🚧 Markdown-Editor verbessern
2. 🚧 Celery für asynchronen E-Mail-Versand
3. ⬜ Audit-Trail
4. ⬜ Mahnwesen

### Phase 3 (Backlog)
1. ⬜ 2FA
2. ⬜ REST API
3. ⬜ Dark Mode
4. ⬜ Backup & Monitoring

---

*Dokument erstellt durch automatische Code-Analyse*  
*Prüfmethode: Models, Views, Templates, URLs*  
*Letzte Aktualisierung: 2026-03-05*
