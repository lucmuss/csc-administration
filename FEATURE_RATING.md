# CSC-Admin Feature-Bewertung

## Legende

| Sterne | Bedeutung |
|--------|-----------|
| ⭐ | Niedrig / Optional |
| ⭐⭐ | Mittel / Wichtig |
| ⭐⭐⭐ | Hoch / Kritisch |

## Bewertungskategorien

1. **Aufwand** (Implementierung + Wartung)
2. **Benutzerfreundlichkeit** (UX für Admins & Mitglieder)
3. **Compliance** (CanG, DSGVO, rechtliche Pflicht)

---

## Feature-Bewertungen

### 🔐 AUThentifizierung & SICHERHEIT

| Feature | Aufwand | UX | Compliance | Gesamt | Begründung |
|---------|---------|----|------------|--------|------------|
| **Login (Basic)** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Standard-Feature, aber essentiell |
| **2-Faktor-Auth (2FA)** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | DSGVO-Pflicht bei sensiblen Daten |
| **Rollen & Berechtigungen** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Vier-Augen-Prinzip, CanG-kritisch |
| **Audit-Trail (Protokoll)** | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | Wer hat was wann geändert - Pflicht! |
| **Session-Management** | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | Automatisches Logout, Sicherheit |

---

### 👥 MITGLIEDERVERWALTUNG

| Feature | Aufwand | UX | Compliance | Gesamt | Begründung |
|---------|---------|----|------------|--------|------------|
| **Mitglied-CRUD** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Kernfunktion, ohne geht nichts |
| **Digitale Ausweise** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Praktisch, aber nicht Pflicht |
| **Altersprüfung (21+)** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | CanG: Mindestalter 21 Jahre |
| **Wohnsitz-Prüfung (6 Monate)** | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | CanG-Pflicht, schwer zu automatisieren |
| **Mitgliedsnummern-Vergabe** | ⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | Automatisch, sequentiell |
| **Doppelmitgliedschaft-Check** | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | CanG: Keine doppelten Mitgliedschaften |
| **Kündigungsfrist-Tracking** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Satzung: 2 Monate Frist |
| **Einwilligungen (DSGVO)** | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Datenschutz-Pflicht |

---

### 💰 FINANZEN & ZAHLUNGEN

| Feature | Aufwand | UX | Compliance | Gesamt | Begründung |
|---------|---------|----|------------|--------|------------|
| **Mitgliedsbeiträge erfassen** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Umsatzsteuer, Buchhaltung |
| **SEPA-Lastschrift** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Automatisierung, aber komplex |
| **SEPA-Mandatsverwaltung** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Rechtlich bindend, Pflicht! |
| **Rückläufer-Handling** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | Mahnwesen, komplex |
| **Mahnwesen (autom.)** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | Praktisch, aber aufwendig |
| **DATEV-Export** | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | Steuerberater braucht das |
| **Kassenbuch** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | GoBD-konforme Buchführung |
| **Rechnungswesen** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | Optionales Modul |

---

### 🌱 ANBAU & LAGER

| Feature | Aufwand | UX | Compliance | Gesamt | Begründung |
|---------|---------|----|------------|--------|------------|
| **Chargen-Verwaltung** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Seed-to-Sale Tracking Pflicht |
| **Growtagebuch** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Dokumentation für Behörden |
| **Sorten-Verwaltung** | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Einfach, aber wichtig |
| **THC/CBD-Erfassung** | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | CanG: Infozettel-Pflicht |
| **MHD-Verwaltung** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Verbrauchsdatum, Rückrufe |
| **Lager-Bestandsklassen** | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | A+, A, B, C - Qualitätsstufen |
| **Inventur-Funktion** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Jährliche Inventur Pflicht |
| **Abfallnachweise** | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | Vernichtung dokumentieren |

---

### 🏷️ AUSGABE & DISTRIBUTION

| Feature | Aufwand | UX | Compliance | Gesamt | Begründung |
|---------|---------|----|------------|--------|------------|
| **Limit-Prüfung (25g/Tag)** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | CanG: Automatisch prüfen & blocken |
| **Limit-Prüfung (50g/Monat)** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | CanG: Monatslimit |
| **Jugendschutz (18-21)** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 30g/Monat, max 10% THC |
| **Pflicht-Infozettel** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Gewicht, Sorte, THC, Warnhinweise |
| **Etiketten-Druck** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Neutral, Pflichtangaben |
| **Quittungen** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Nachweis für Mitglied |
| **Transportbescheinigungen** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Übergabe an Mitglieder |
| **Reservierungssystem** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | Komfort, aber nicht Pflicht |

---

### 📊 REPORTS & COMPLIANCE

| Feature | Aufwand | UX | Compliance | Gesamt | Begründung |
|---------|---------|----|------------|--------|------------|
| **Behörden-Exporte** | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Monatliche Meldungen Pflicht |
| **Verdachtsanzeigen** | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | Bei Auffälligkeiten |
| **Finanz-Berichte** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Vorstand, Jahresabschluss |
| **Dashboard/Statistiken** | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | Übersicht für Admins |
| **Präventions-Berichte** | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | Eigenentwicklung, wichtig |

---

### 🔔 KOMMUNIKATION

| Feature | Aufwand | UX | Compliance | Gesamt | Begründung |
|---------|---------|----|------------|--------|------------|
| **E-Mail-Versand** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Automatisierung |
| **Newsletter** | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | Marketing, optional |
| **Mitgliederversammlung** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Satzung: Einladungspflicht |
| **Push-Benachrichtigungen** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | Mobile App nötig |

---

### 📱 MOBILE & ZUSATZ

| Feature | Aufwand | UX | Compliance | Gesamt | Begründung |
|---------|---------|----|------------|--------|------------|
| **Mobile App (iOS/Android)** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | Komfort, aber nicht Pflicht |
| **API für Integrationen** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | Für externe Tools |
| **Barcode/QR-Scanning** | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | Schnellere Ausgabe |
| **KI-Assistent** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | Nice-to-have (wie Cannanas) |
| **Community-Features** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | Social, optional |
| **Multi-Tenant** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | Für mehrere Clubs |

---

## 🎯 PRIORISIERUNGSEMPFEHLUNG

### MUST-HAVE (Sofort implementieren)
| Feature | Priorität |
|---------|-----------|
| Rollen & Berechtigungen | ⭐⭐⭐ |
| Audit-Trail | ⭐⭐⭐ |
| Mitglied-CRUD | ⭐⭐⭐ |
| Limit-Prüfung (25/50g) | ⭐⭐⭐ |
| Pflicht-Infozettel | ⭐⭐⭐ |
| Chargen-Verwaltung | ⭐⭐⭐ |
| Behörden-Exporte | ⭐⭐⭐ |
| SEPA-Mandatsverwaltung | ⭐⭐⭐ |
| Kassenbuch | ⭐⭐⭐ |

### SHOULD-HAVE (Phase 2)
| Feature | Priorität |
|---------|-----------|
| 2FA | ⭐⭐ |
| Growtagebuch | ⭐⭐ |
| Transportbescheinigungen | ⭐⭐ |
| Mahnwesen | ⭐⭐ |
| Mobile App | ⭐⭐ |
| API | ⭐⭐ |

### NICE-TO-HAVE (Später)
| Feature | Priorität |
|---------|-----------|
| KI-Assistent | ⭐ |
| Community-Features | ⭐ |
| Hardware-Integration | ⭐ |
| Cannabis Cup Voting | ⭐ |

---

## 💡 IMPLEMENTIERUNGSRATGEBER

### MVP (3-4 Monate)
Fokus auf **Compliance-kritische Features** (alle mit ⭐⭐⭐ in Compliance):
- Mitgliederverwaltung + Limits
- Chargen + Ausgabe + Infozettel
- Finanzen (Basis) + Kassenbuch
- Reports für Behörden

### Phase 2 (2-3 Monate)
**Benutzerfreundlichkeit** verbessern:
- Mobile App
- 2FA + Audit-Trail
- Automatisierung (Mahnen, Reports)
- API

### Phase 3 (Kontinuierlich)
**Differentierung** vom Wettbewerb:
- KI-Features
- Community
- Multi-Tenant

---

**Erstellt am:** 2. März 2026
**Bewertung basiert auf:** CanG, DSGVO, Satzung CSC Leipzig Süd, Wettbewerbsanalyse
