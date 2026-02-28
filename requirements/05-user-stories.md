# User Stories - CSC-Admin

## Rollen
1. **Vorstand/Admin** - Voller Zugriff, Verantwortung
2. **Mitarbeiter** - Ausschank, Mitgliederservice
3. **Mitglied** - Nur eigene Daten sehen
4. **Behörde** (read-only) - Prüfrechte

---

## Als Vorstand/Admin möchte ich...

### Mitgliederverwaltung
- [ ] Ein neues Mitglied registrieren mit allen Daten
- [ ] Den 6-Monats-Probemonitoring starten
- [ ] Ein Mitglied sperren (z.B. bei Verstoß)
- [ ] Die Mitgliederliste exportieren
- [ ] Sehen wie viele Mitglieder wir aktuell haben
- [ ] Mitgliedsbeiträge einsehen und verwalten

### Ausschank
- [ ] Den täglichen Ausschank limitieren (25g)
- [ ] Den monatlichen Verbrauch eines Mitglieds sehen
- [ ] Bei Überschreitung blockieren (mit Begründung)
- [ ] Chargen-Informationen beim Ausschank erfassen
- [ ] Einen Ausschank rückgängig machen (Fehlklick)

### Bestand
- [ ] Neue Charge einbuchen (Herkunft, Menge, THC)
- [ ] Aktuellen Bestand sehen
- [ ] Warnung bei niedrigem Bestand
- [ ] Inventur durchführen

### Compliance
- [ ] Monatlichen BOPST-Report generieren
- [ ] Audit-Log einsehen (wer hat wann was gemacht?)
- [ ] Bei Polizeikontrolle alle Daten bereitstellen

### Buchhaltung
- [ ] Spenden einbuchen
- [ ] Ausgaben erfassen
- [ ] Finanzbericht für Vorstand erstellen
- [ ] Daten für Steuerberater exportieren

---

## Als Mitarbeiter möchte ich...

### Ausschank
- [ ] Schnell nach Mitglied suchen (Name oder Nummer)
- [ ] Verfügbare Menge sehen (Tages/Monats-Limit)
- [ ] Mit QR-Code oder NFC-Karte identifizieren
- [ ] Quittung drucken oder per Mail senden
- [ ] Bei Problemen Admin alarmieren

### Mitgliederservice
- [ ] Mitgliedsdaten aktualisieren
- [ ] Mitglied über Status informieren
- [ ] Fragen zu Limits beantworten

---

## Als Mitglied möchte ich...

### Selbstservice (Mitgliederbereich)
- [ ] Meine Stammdaten einsehen und aktualisieren
- [ ] Meinen Verbrauch sehen (dieser Monat)
- [ ] Meine Beitragszahlungen einsehen
- [ ] Mein Mitgliedschafts-Status sehen
- [ ] Kontaktdaten zum Verein finden

### Transparenz
- [ ] Welche Sorten gibt es aktuell?
- [ ] Wie viel habe ich diesen Monat schon abgeholt?
- [ ] Wann kann ich wieder abholen?

---

## Als Behörde (BOPST/Polizei) möchte ich...

### Prüfung
- [ ] Liste aller Mitglieder sehen (anonymisiert)
- [ ] Gesamtabgaben pro Monat sehen
- [ ] Stichprobenweise Ausschank-Logs prüfen
- [ ] Sehen ob Limits eingehalten wurden

### Rechtssicherheit
- [ ] Nachweis der 6-Monats-Regel sehen
- [ ] Dokumentation des Anbaus prüfen
- [ ] Audit-Trail nachvollziehen

---

## Priorisierung (MVP)

### Muss (P0)
- Mitgliederverwaltung
- Ausschank mit Limits (25g/Tag, 50g/Monat)
- Bestandsverwaltung
- Audit-Log

### Soll (P1)
- Mitgliederservice (online)
- Automatische Reports
- Buchhaltung

### Kann (P2)
- App für Mitglieder
- QR-Code System
- Labor-Integration (THC-Tests)

---

## Akzeptanzkriterien (Beispiele)

### Story: "Als Mitarbeiter möchte ich schnell nach Mitglied suchen"
**Kriterien:**
- Suche funktioniert nach Name, Mitgliedsnummer, oder Telefonnummer
- Ergebnis wird in < 2 Sekunden angezeigt
- Mitglieds-Status wird angezeigt (aktiv/gesperrt/Probezeit)
- Tages- und Monatsverbrauch wird angezeigt
- Bei Limit-Erreichnung wird rot markiert

### Story: "Als Admin möchte ich monatlichen BOPST-Report generieren"
**Kriterien:**
- Report enthält: Anzahl Mitglieder, Gesamtmenge abgegeben
- Format ist PDF und CSV
- Automatische Generierung möglich
- Historie der Reports ist verfügbar