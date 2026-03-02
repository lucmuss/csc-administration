# User Stories - CSC Admin System

> Aus der Perspektive verschiedener Nutzerrollen
> Stand: 2. März 2026

---

## 👤 Mitglieder (Endnutzer)

### US-001: Registrierung
**Als** potenzielles Mitglied  
**möchte ich** mich online für den CSC bewerben  
**damit** ich Mitglied werden kann.

**Akzeptanzkriterien:**
- [ ] Ich kann ein Formular mit meinen Daten ausfüllen
- [ ] Ich muss bestätigen, dass ich 21+ bin und in Deutschland wohne
- [ ] Ich erhalte eine Bestätigungs-E-Mail mit den Unterlagen
- [ ] Ich habe 8 Wochen Zeit, die Registrierung abzuschließen
- [ ] Meine Daten werden DSGVO-konform verarbeitet

---

### US-002: Einloggen & Dashboard sehen
**Als** Mitglied  
**möchte ich** mich einloggen und meine Übersicht sehen  
**damit** ich meinen Status und meine Limits prüfen kann.

**Akzeptanzkriterien:**
- [ ] Login mit E-Mail und Passwort
- [ ] Anzeige meines Guthabens
- [ ] Anzeige verbrauchter Limits (Monat/Tag)
- [ ] Übersicht vergangener Bestellungen
- [ ] Download meines digitalen Mitgliedsausweises

---

### US-003: Sorten browsen & bestellen
**Als** Mitglied  
**möchte ich** verfügbare Sorten sehen und bestellen  
**damit** ich Cannabis abholen kann.

**Akzeptanzkriterien:**
- [ ] Liste aller verfügbaren Sorten mit Preisen
- [ ] Filter nach Typ (Blüten/Stecklinge)
- [ ] Anzeige meiner verfügbaren Menge (Limit-Check)
- [ ] Warenkorb mit Mengenauswahl
- [ ] Warnung bei Limit-Überschreitung
- [ ] Reservierung für max. 48h

---

### US-004: Abholung
**Als** Mitglied  
**möchte ich** meine bestellte Ware abholen  
**damit** ich sie erhalten kann.

**Akzeptanzkriterien:**
- [ ] QR-Code oder Ausweis-Scan an der Abholstation
- [ ] Automatische Limit-Aktualisierung
- [ ] Unterschrift auf Tablet/Stift
- [ ] Quittung per E-Mail
- [ ] Option: Bevollmächtigter kann für mich abholen

---

### US-005: Zahlung
**Als** Mitglied  
**möchte ich** meine Mitgliedsbeiträge und Abgaben bezahlen  
**damit** ich mein Guthaben auflade.

**Akzeptanzkriterien:**
- [ ] Übersicht offener Posten
- [ ] Zahlung per SEPA-Lastschrift (wenn Mandat vorhanden)
- [ ] Zahlung per Überweisung (Bankdaten angezeigt)
- [ ] Zahlung per Bar bei Abholung
- [ ] Zahlungsbestätigung per E-Mail

---

### US-006: Mitgliederversammlung
**Als** Mitglied  
**möchte ich** zu Mitgliederversammlungen eingeladen werden  
**damit** ich teilnehmen kann.

**Akzeptanzkriterien:**
- [ ] Einladung per E-Mail 14 Tage vorher
- [ ] Erinnerung 2 Tage vorher
- [ ] Kalender-Datei (.ics) zum Download
- [ ] Online-Teilnahme-Link (Google Meet)
- [ ] Tagesordnung einsehbar

---

## 👔 Vorstand / Administrator

### US-007: Mitglieder akzeptieren
**Als** Vorstand  
**möchte ich** neue Mitglieder akzeptieren oder ablehnen  
**damit** nur qualifizierte Mitglieder aufgenommen werden.

**Akzeptanzkriterien:**
- [ ] Liste aller ausstehenden Anträge
- [ ] Einzelansicht mit allen Dokumenten
- [ ] Prüfung: Alter, Wohnsitz, Duplikate
- [ ] Akzeptieren/Ablehnen mit Begründung
- [ ] Automatische E-Mail an Mitglied
- [ ] Generierung der Mitgliedsnummer

---

### US-008: Mitglieder verifizieren
**Als** Vorstand  
**möchte ich** Mitglieder verifizieren  
**damit** ihre Identität bestätigt ist.

**Akzeptanzkriterien:**
- [ ] Status-Tracking: Dokumente eingereicht → In Prüfung → Video-Call → Verifiziert
- [ ] Upload von Ausweis und Wohnsitznachweis
- [ ] Video-Call-Termin vereinbaren
- [ ] Erinnerung nach 14 Tagen ohne Fortschritt
- [ ] Automatische Freischaltung nach Verifizierung

---

### US-009: Finanz-Übersicht
**Als** Kassierer  
**möchte ich** die Finanzen überblicken  
**damit** ich die Buchhaltung führen kann.

**Akzeptanzkriterien:**
- [ ] Dashboard mit Umsatz (Tag/Monat/Quartal)
- [ ] Liste offener Posten
- [ ] SEPA-Lastschriften auslösen
- [ ] Mahnungen versenden
- [ ] Export für Steuerberater (DATEV)

---

### US-010: Chargen erfassen
**Als** Mitarbeiter  
**möchte ich** neue Ernten/Chargen ins System einpflegen  
**damit** sie für Mitglieder verfügbar sind.

**Akzeptanzkriterien:**
- [ ] Charge anlegen mit Sorte, Menge, Erntedatum
- [ ] THC/CBD-Werte erfassen
- [ ] Qualitätsstufe zuweisen (A+, A, B)
- [ ] MHD eingeben
- [ ] Bestand wird automatisch aktualisiert
- [ ] Mitglieder werden über neue Sorte informiert

---

### US-011: Ausgabe durchführen
**Als** Mitarbeiter  
**möchte ich** Cannabis an Mitglieder ausgeben  
**damit** der Bestand korrekt abgebucht wird.

**Akzeptanzkriterien:**
- [ ] QR-Code-Scan des Mitgliedsausweises
- [ ] Anzeige verfügbarer Limits
- [ ] Auswahl der Charge/Sorte
- [ ] Automatische Limit-Prüfung
- [ ] Unterschrift des Mitglieds
- [ ] Quittungsdruck
- [ ] Transportbescheinigung generieren

---

### US-012: Reports erstellen
**Als** Vorstand  
**möchte ich** Berichte für Behörden erstellen  
**damit** wir compliant sind.

**Akzeptanzkriterien:**
- [ ] Monatliche Abgabe-Reports
- [ ] Verdachtsanzeigen bei Auffälligkeiten
- [ ] Inventur-Berichte
- [ ] Export als PDF/CSV
- [ ] Automatische Archivierung

---

## 🔧 System-Administrator

### US-013: System konfigurieren
**Als** Admin  
**möchte ich** Systemeinstellungen anpassen  
**damit** der Club flexibel bleibt.

**Akzeptanzkriterien:**
- [ ] Preise ändern
- [ ] Mitgliederversammlungstermine festlegen
- [ ] E-Mail-Templates bearbeiten
- [ ] Benachrichtigungs-Einstellungen
- [ ] Backup-Einstellungen

---

### US-014: Backup & Wiederherstellung
**Als** Admin  
**möchte ich** Backups verwalten  
**damit** keine Daten verloren gehen.

**Akzeptanzkriterien:**
- [ ] Tägliches automatisches Backup
- [ ] Manuelles Backup auslösen
- [ ] Wiederherstellung testen
- [ ] Backup-Status einsehen

---

## 📊 Zusammenfassung

| Rolle | Anzahl User Stories |
|-------|---------------------|
| Mitglied | 6 |
| Vorstand/Admin | 6 |
| Mitarbeiter | 2 |
| System-Admin | 2 |
| **Gesamt** | **16** |

---

**Priorisierung:**

**MVP (Must-Have):**
- US-001 (Registrierung)
- US-002 (Login/Dashboard)
- US-003 (Bestellung)
- US-007 (Mitglieder akzeptieren)
- US-011 (Ausgabe)

**Phase 2:**
- US-004 (Abholung mit QR)
- US-005 (Zahlung)
- US-008 (Verifizierung)
- US-009 (Finanzen)
- US-010 (Chargen)

**Phase 3:**
- US-006 (Mitgliederversammlung)
- US-012 (Reports)
- US-013 (Konfiguration)
- US-014 (Backup)
