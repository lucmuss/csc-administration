# Deutsches CSC-Recht (KannG)

## Gesetzliche Grundlage
**Cannabisgesetz (KannG)** - In Kraft seit April 2024

## Kernpunkte für CSCs

### 1. Mitgliedschaft
- **Mindestalter**: 18 Jahre
- **Mindestmitgliedschaft**: 6 Monate vor erstem Zugang
- **Max Mitglieder**: 500 pro Club
- **Mitgliedschaft**: Muss aktiv sein (nicht nur "Konsum-Mitglied")
- **Austritt**: Jederzeit möglich

### 2. Abgabemengen (wichtig für Software!)
- **Pro Tag**: Max 25g pro Mitglied
- **Pro Monat**: Max 50g pro Mitglied
- **Pro Abgabe**: Max 25g (d.h. max 1x pro Tag)
- **Obergrenze**: 30g THC pro Monat (wenn THC-Gehalt bekannt)

### 3. Abgabe-Regeln
- **Kein Verkauf**: Nur "Ausschank" gegen Kostendeckung
- **Spendenbasis**: Mitglieder spenden für Kosten, nicht für Cannabis
- **Persönlich**: Mitglied muss persönlich abholen (keine Vertretung)
- **Ausweis**: Identitätsprüfung erforderlich

### 4. Dokumentationspflichten (für Software!)
**Muss dokumentiert werden:**
- [ ] Wer hat wann wie viel abgeholt?
- [ ] Woher stammt das Cannabis (Anbau)?
- [ ] THC-Gehalt (wenn bekannt)
- [ ] Chargen-Nummern
- [ ] Mitglieds-Nr. bei jeder Abgabe

**Aufbewahrungsfristen:**
- Abgabedaten: 2 Jahre
- Mitgliedsdaten: 2 Jahre nach Austritt
- Buchhaltung: 10 Jahre

### 5. Anbau
- Max 500 Pflanzen pro Club
- Nur für Mitglieder
- Kein Verkauf außerhalb
- Dokumentation: Sorte, Menge, Anbau-Datum

### 6. Meldungen an Behörden
**Bundesopiumstelle (BOPST):**
- Anzahl Mitglieder (monatlich)
- Gesamtmenge Abgaben (monatlich)
- Bei Verdacht auf Weiterverkauf sofort

**Zoll:**
- Bei Import von Samen/Sämlingen
- Dokumentation Herkunft

## Konsequenzen bei Verstoß
- Club-Schließung möglich
- Strafrechtliche Verfolgung
- Geldstrafen
- Verlust der Gemeinnützigkeit

## Software-Implikationen

### Hard Limits (MÜSSEN eingehalten werden)
```python
MAX_DAILY_GRAMS = 25
MAX_MONTHLY_GRAMS = 50
MAX_MONTHLY_THC_MG = 30000  # 30g THC
MIN_MEMBERSHIP_MONTHS = 6
MAX_MEMBERS = 500
```

### Audit-Trail (Muss nachvollziehbar sein)
- Jede Abgabe mit Zeitstempel
- Wer hat genehmigt?
- Mitglieds-Status geprüft?
- Limits eingehalten?

### Reporting
- Monatlicher Report an BOPST
- Jährlicher Finanzbericht
- Mitgliederliste (aktualisiert)
- Bestandsübersicht

## Recherche-ToDo
- [ ] Kontakt zu CSC-Vereinen für praktische Einblicke
- [ ] Anwalt konsultieren für rechtssichere Formulierungen
- [ ] BOPST-Richtlinien genau studieren
- [ ] Datenschutzbehörde konsultieren (DSGVO + Cannabis-Daten)