# CSC-Administration - Dokumenten-Index

> Master-Übersicht aller Projekt-Dokumente
> Stand: 2. März 2026

---

## 📁 Dokumenten-Struktur

### 1. Kern-Dokumente (Pflichtlektüre)

| Dokument | Zweck | Letzte Änderung |
|----------|-------|-----------------|
| **[REQUIREMENTS.md](./REQUIREMENTS.md)** | Vollständige System-Anforderungen | 02.03.2026 |
| **[COMPETITOR_ANALYSIS.md](./COMPETITOR_ANALYSIS.md)** | Wettbewerbsanalyse (3 Anbieter) | 01.03.2026 |
| **[COMPETITOR_DEEP_ANALYSIS.md](./COMPETITOR_DEEP_ANALYSIS.md)** | Tiefenanalyse (17 Anbieter) | 02.03.2026 |
| **[FEATURE_RATING.md](./FEATURE_RATING.md)** | Feature-Bewertung (Aufwand/UX/Compliance) | 02.03.2026 |

### 2. Daten & Schema

| Dokument | Zweck |
|----------|-------|
| **[database_schema.sql](./database_schema.sql)** | SQL-Schema (Tabellen, Beziehungen) |
| **[import_members.py](./import_members.py)** | CSV-Import-Skript |
| **[seed_data/members.csv](./seed_data/members.csv)** | 55 anonymisierte Test-Mitglieder |
| **[seed_data/strains.csv](./seed_data/strains.csv)** | 16 Sorten (Blüten + Stecklinge) |

### 3. Templates & Beispiele

| Dokument | Zweck |
|----------|-------|
| **[cdata/member_template.json](./cdata/member_template.json)** | Mitglied-JSON-Struktur |
| **[cdata/strains.json](./cdata/strains.json)** | Sorten-JSON-Struktur |
| **[cdata/order_template.json](./cdata/order_template.json)** | Bestellungs-JSON-Struktur |

### 4. Legacy (Referenz)

| Ordner | Inhalt |
|--------|--------|
| **[legacy/appscripts/](./legacy/appscripts/)** | 6 Google Appscripts (FormSubmit, RestLimitDay, etc.) |
| **[legacy/forms/](./legacy/forms/)** | Google Formulare (Mitgliedsantrag, Bestellung) |
| **[legacy/emails/](./legacy/emails/)** | E-Mail-Templates mit PDF-Anhängen |

### 5. Automatisierung

| Datei | Zweck |
|-------|-------|
| **[scripts/auto-git-sync.sh](./scripts/auto-git-sync.sh)** | Automatisches Git-Backup (täglich 23:00) |

---

## 📊 REQUIREMENTS.md - Abschnitts-Übersicht

| Abschnitt | Inhalt | Kritisch |
|-----------|--------|----------|
| **1. Übersicht** | Projektbeschreibung, Scope | ✅ |
| **2. Kernfunktionen** | Mitgliederverwaltung, Bestellsystem, Inventar, Finanzen, RBAC | ✅ |
| **3. Datenmodell** | Entitäten, JSON-Templates, Backup-Strategie | ✅ |
| **4. Import/Export** | CSV-Import, Export-Formate, IBAN-Validierung | ✅ |
| **5. Technische Anforderungen** | Backend, Frontend, Sicherheit | ✅ |
| **6. Rechtliche Anforderungen** | CanG, DSGVO, SEPA, Verdachtsanzeige | ✅ |
| **7. UI/UX** | Dashboard, Mobile, Design | |
| **8. Integrationen** | Zahlungsanbieter, Kommunikation, Kalender | |
| **9. Reports** | Statistiken, Finanzen | |
| **10. Prioritäten** | MVP, Phase 2, Phase 3 | ✅ |
| **11. Datei-Struktur** | Projekt-Layout | |
| **12. Entwickler-Hinweise** | Excel-Import, Limit-Prüfung, Sicherheit | |

### Erweiterte Abschnitte (7.x)

| Abschnitt | Features | Quelle |
|-----------|----------|--------|
| **7.1 Sicherheit** | 2FA, Audit-Trail, Session-Mgmt, Breach-Notification | Competitor-Analyse |
| **7.2 Mitgliederverwaltung** | Digitale Ausweise, Doppelmitgliedschaft-Check, Verifizierungs-Workflow | Competitor-Analyse |
| **7.3 Finanzen** | SEPA-Workflows, Mahnwesen, DATEV, USt-Split, Spenden | Competitor-Analyse |
| **7.4 Anbau & Lager** | Growtagebuch, Chargen, Pflanzen-Tracking, Schädlings-Protokoll | Competitor-Analyse |
| **7.5 Ausgabe** | Transportbescheinigungen, Reservierung, Warteliste, Express-Abholung | Competitor-Analyse |
| **7.6 Mobile App** | iOS/Android, Offline-Modus, Dark Mode, Biometrie | Competitor-Analyse |
| **7.7 API & Integrationen** | REST API, SMS-Gateway, DATEV | Competitor-Analyse |
| **7.8 Community** | Forum, Chat, Events (optional) | Competitor-Analyse |
| **7.9 Admin-Panel** | Konfigurationsoberfläche, Delta-T Slider, Multi-Language | User-Request |
| **7.10 Fallstricke** | 12 kritische Warnungen (rechtlich, technisch, organisatorisch) | Claude-Analyse |

---

## 🎯 Feature-Status

### Implementiert in Requirements
- [x] **MVP-Features**: 25+ Kernfunktionen definiert
- [x] **Erweiterte Features**: 40+ aus Competitor-Analyse
- [x] **Compliance**: CanG, DSGVO, SEPA abgedeckt
- [x] **Sicherheit**: 2FA, Audit-Trail, Verschlüsselung
- [x] **Mobile**: App-Konzept (iOS/Android)
- [x] **Automatisierung**: Cronjobs, Workflows
- [x] **Fallstricke**: 12 kritische Warnungen dokumentiert

### Ausstehend (Konzept/Design)
- [ ] UI/UX-Mockups (Wireframes)
- [ ] API-Spezifikation (OpenAPI)
- [ ] Datenbank-Optimierung (Indizes, Queries)
- [ ] Deployment-Guide (Docker, Server)
- [ ] Testing-Strategie (Unit, Integration, E2E)

---

## 🔗 Wichtige Verweise

### Externe Ressourcen
- **Website**: https://www.csc-leipzig.eu
- **Satzung**: [Google Docs](https://docs.google.com/document/d/e/2PACX-1vTjc1aS_Z4239XTGpgS1DxTbuI3bWtClVhWE6yWIUvIO2VHT0PAsx8qRcg-KxwKvHhMHJVPTxsHls_G/pub)
- **GitHub**: https://github.com/lucmuss/csc-administration

### Competitor-Links (Analyse-Basis)
- **Hanf-App**: https://diehanfapp.de/
- **Cannanas**: https://cannanas.club/
- **Vergleichsportale**: Siehe COMPETITOR_DEEP_ANALYSIS.md

---

## 📝 Änderungshistorie

| Datum | Änderung | Autor |
|-------|----------|-------|
| 01.03.2026 | Initiale Requirements | Biodanza |
| 01.03.2026 | Competitor-Analyse (Basis) | Biodanza |
| 02.03.2026 | Tiefenanalyse (17 Anbieter) | Biodanza |
| 02.03.2026 | Feature-Bewertung | Biodanza |
| 02.03.2026 | Abschnitt 7.x (40+ Features) | Biodanza + Claude |
| 02.03.2026 | Admin-Panel Konfiguration | User + Biodanza |
| 02.03.2026 | Kritische Fallstricke (12x) | Claude-Analyse |
| 02.03.2026 | Abschnitte 1-6 Fixes | Claude-Analyse |

---

## 🚀 Nächste Schritte

1. **Tech-Stack Entscheidung** (Django vs Node.js)
2. **Datenbank-Schema finalisieren**
3. **UI/UX Wireframes erstellen**
4. **MVP-Implementierung starten**

---

**Kontakt**: Lucas Leipzig (@lucas_leipzig)
**Letzte Aktualisierung**: 2. März 2026, 04:30 Uhr
