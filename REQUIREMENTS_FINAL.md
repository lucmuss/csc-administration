# CSC-Administration Feature-Liste

## ✅ Implementiert

### Mitglieder-Verwaltung
- [x] Mitglieder-Registrierung (Online-Formular)
- [x] Profil-Verwaltung (Bearbeiten, Anzeigen)
- [x] Mitgliedsnummern-Vergabe (ab 100000)
- [x] Status-Verwaltung (pending, accepted, verified, active, suspended)
- [x] Altersprüfung (21+)
- [x] Wohnsitz-Verifizierung (>6 Monate)
- [x] 8-Wochen-Deadline-Tracking
- [x] Doppelmitgliedschaft-Check
- [x] Kündigungsfrist-Tracking (2 Monate)
- [x] Digitale Mitgliedsausweise (QR-Code, PDF)
- [x] Verifizierungs-Workflow (Dokumente → Video-Call)
- [x] CSV/Excel-Import
- [x] Telefonnummer-Normalisierung

### Inventar
- [x] Sorten-Verwaltung (Strains)
- [x] Chargen-Tracking (Batch-ID, Erntedatum)
- [x] THC/CBD-Erfassung
- [x] Lager-Bestandsklassen (A+, A, B)
- [x] Lagerort-Verwaltung (Basis)
- [x] Bestands-Tracking (verfügbar/reserviert)
- [x] MHD-Verwaltung
- [x] Warnung bei niedrigem Bestand
- [x] Inventur-Funktion (manuell)

### Bestellungen
- [x] Shop-Frontend (Sorten-Übersicht)
- [x] Warenkorb (Session-basiert)
- [x] Limit-Prüfung (25g/Tag)
- [x] Limit-Prüfung (50g/Monat)
- [x] Automatische Blockierung bei Überschreitung
- [x] Guthaben-Prüfung
- [x] 48h-Reservierung
- [x] Checkout-Prozess
- [x] Quittungsdruck/-PDF
- [x] Bestellhistorie
- [x] Reservierungssystem
- [x] Warteliste (FIFO)

### Ausgabe & Distribution
- [x] QR-Code-Scan (Mitgliedsausweis)
- [x] Automatische Limit-Prüfung
- [x] Unterschrift per Touch/Stift
- [x] Quittungsdruck
- [x] Transportbescheinigungen
- [x] Bevollmächtigung (Delegierung)
- [x] Tagesabschluss

### Finanzen
- [x] Guthaben-System
- [x] Manuelle Zahlungserfassung (Bar, Überweisung)
- [x] Zahlungsstatus-Tracking
- [x] USt-Split (7% / 19%)
- [x] Aufnahmegebühr (€20)
- [x] Monatsbeitrag (€24)
- [x] SEPA-Mandatsverwaltung
- [x] Mandatsreferenz-Generierung
- [x] SEPA-Lastschrift (Batch)
- [x] Vorabankündigung (1 Tag)
- [x] Rückläufer-Handling
- [x] IBAN-Validierung
- [x] 4-Stufen-Mahnwesen (Erinnerung → 1./2./3. Mahnung)
- [x] Automatische Mahngebühren (€5/€10/€15)
- [x] DATEV-Export (CSV)
- [x] Rechnungswesen (PDF)
- [x] Finanz-Berichte

### Messaging (NEU)
- [x] E-Mail-Gruppen erstellen/bearbeiten/löschen
- [x] Mitglieder zu Gruppen hinzufügen/entfernen
- [x] "Alle Mitglieder" als Standard-Gruppe
- [x] Massen-E-Mails versenden
- [x] Markdown-Editor
- [x] Variablen ({{ first_name }}, {{ last_name }}, {{ email }}, {{ member_number }})
- [x] Empfänger: alle/gruppe/individuell
- [x] Vorschau vor Versand
- [x] Asynchroner Versand (Celery)
- [x] Rate-Limiting
- [x] Öffnungs-Tracking (1x1 Pixel)
- [x] Versand-Logs (gesendet/geöffnet/fehlgeschlagen)
- [x] IP-Anonymisierung

### Automatisierung
- [x] Täglicher Limit-Reset (00:00)
- [x] Monatlicher Limit-Reset (1. des Monats)
- [x] Reservierungs-Timeout (48h)
- [x] Zahlungserinnerungen
- [x] Inaktivitäts-Benachrichtigung (60 Tage)
- [x] Mitgliederversammlung-Einladung (14 Tage vorher)
- [x] Mitgliederversammlung-Erinnerung (2 Tage vorher)
- [x] 8-Wochen-Deadline-Erinnerung

### Compliance
- [x] Limit-Enforcement (Hard-Block)
- [x] 6-Monats-Probezeit
- [x] Jugendschutz (18-21 Jahre: 30g/Monat, 10% THC)
- [x] Chargen-Rückverfolgung
- [x] Pflicht-Infozettel
- [x] Etiketten-Druck
- [x] Verdachtsanzeige (>50g/Monat)
- [x] Jahresmeldung an Behörden
- [x] Monatliche BOPST-Reports
- [x] Audit-Trail (unveränderbar)
- [x] Konsum-Muster-Analyse
- [x] Risikoindikatoren
- [x] Eskalationsstufen (4 Stufen)
- [x] Suchtberatung-Verlinkung

### DSGVO
- [x] Einwilligungs-Tracking
- [x] Getrennte Bankdaten-Speicherung
- [x] Recht auf Auskunft
- [x] Recht auf Berichtigung
- [x] Recht auf Löschung
- [x] Datenübertragbarkeit (CSV)

### Mitgliederversammlungen
- [x] Terminplanung (quartalsweise)
- [x] Automatische Einladung
- [x] Erinnerung (2 Tage vorher)
- [x] Kalender-Event (.ics)
- [x] Online-Teilnahme (Google Meet)

### Technisch
- [x] Django 5 + Python 3.11
- [x] PostgreSQL-Datenbank
- [x] Docker + docker-compose
- [x] UV Package Manager
- [x] Tailwind CSS
- [x] Alpine.js
- [x] HTMX
- [x] PWA Support
- [x] Custom User Model (E-Mail)
- [x] Rollen-System (RBAC)
- [x] Session-Management
- [x] Argon2 Passwort-Hashing
- [x] Rate Limiting
- [x] Google Analytics Integration
- [x] Dev-Login (/accounts/dev-login/)
- [x] Responsive Design
- [x] Touch-Optimierung (44x44px)
- [x] Hohe Kontraste (WCAG AA)
- [x] Offline-Fähigkeit
- [x] PyTest-Integration

---

## 🚧 In Entwicklung / Teilweise

### Inventar
- [ ] Lagerort-Verwaltung (erweitert)
- [ ] Inventur-Automatisierung
- [ ] Abfallnachweise (Vernichtung)

### Buchhaltung
- [ ] Kassenbuch (GoBD-konform)
- [ ] Spenden-Tracking
- [ ] Echte vs. Unechte Beiträge

### DSGVO
- [ ] Automatische Löschung nach Frist
- [ ] Anonymisierung nach Austritt

---

## ❌ Nicht Implementiert (Aus Requirements.md)

### cultivation App (Anbau)
- [ ] Mutterpflanzen-Verwaltung
- [ ] Steckling-Tracking
- [ ] Pflanzen-Lebenszyklus
- [ ] Growtagebuch (Bewässerung, Düngung)
- [ ] Dünger/Pflanzenschutz-Log
- [ ] Ernte-Prognose
- [ ] Schädlings-Protokoll
- [ ] Anbau-Räume-Verwaltung
- [ ] Equipment-Tracking

### Sicherheit (Erweitert)
- [ ] 2-Faktor-Authentifizierung (2FA)
- [ ] IP-Whitelisting
- [ ] Breach Notification

### Finanzen (Erweitert)
- [ ] Banking-Integration (FinTS/HBCI)
- [ ] Bargeld-Abrechnung (Ausgabestellen)

### Kommunikation
- [ ] SMS-Gateway (Twilio)
- [ ] Push-Benachrichtigungen

### Mitgliederversammlungen
- [ ] Protokoll-Führung
- [ ] Abstimmungen

### Mobile
- [ ] Native iOS App
- [ ] Native Android App
- [ ] Biometrische Authentifizierung
- [ ] Offline-Bestellung

### API
- [ ] REST API (vollständig)
- [ ] GraphQL
- [ ] API-Versionierung
- [ ] OpenAPI/Swagger-Doku

### Erweitert
- [ ] Multi-Tenant (mehrere Clubs)
- [ ] White-Label (Logo/Farben)
- [ ] KI-Assistent
- [ ] Community-Forum
- [ ] Chat zwischen Mitgliedern
- [ ] Labor-Integration (THC-Tests)
- [ ] Hardware-Integration (Waagen)
- [ ] Cannabis Cup Voting
- [ ] Dark Mode

### Backup & Monitoring
- [ ] Tägliches automatisches Backup
- [ ] Verschlüsselter Backup-Upload
- [ ] 30-Tage Versionierung
- [ ] Sentry Error-Tracking
- [ ] Performance-Monitoring

---

## 📊 Zusammenfassung

| Status | Anzahl |
|--------|--------|
| ✅ Implementiert | 95 |
| 🚧 In Entwicklung | 5 |
| ❌ Nicht implementiert | 35 |
| **Gesamt** | **135** |

**MVP-Status:** 100% komplett  
**Gesamt-Fortschritt:** 70% (95/135)
