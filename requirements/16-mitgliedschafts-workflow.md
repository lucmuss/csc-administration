# Mitgliedschafts-Workflow & Anmeldung

**Dokumentation:** Workflow für neue Mitglieder

---

## Anmelde-Prozess (Step-by-Step)

### Schritt 1: Online-Anmeldung (Mitglied)
- • Online-Formular ausfüllen
- • Persönliche Daten eingeben (Name, Adresse, Geburtsdatum)
- • Ausweis hochladen (Altersverifikation 18+)
- • Kontaktdaten (E-Mail, Telefon)
- • Wohnort bestätigen (muss in Deutschland sein)
- • Einverständniserklärung akzeptieren (DSGVO)
- • Regeln/Satzung akzeptieren

### Schritt 2: Automatische Validierung (System)
- • Pflichtfelder prüfen
- • E-Mail-Format validieren
- • Alter prüfen (18+ via Geburtsdatum)
- • Maximale Mitgliederzahl prüfen (Limit: 500)
- • Doublette-Check (E-Mail bereits vorhanden?)
- • Automatische Bestätigungs-E-Mail senden

**E-Mail an Bewerber:**
```
Betreff: Mitgliedschaftsantrag erhalten - CSC [Club-Name]

Hallo [Name],

vielen Dank für deine Mitgliedschaftsanfrage bei [Club-Name].

Dein Antrag ist bei uns eingegangen und wird nun vom Vorstand geprüft.
Dies kann bis zu 7 Tage dauern.

Sobald eine Entscheidung getroffen wurde, wirst du von uns benachrichtigt.

Mit freundlichen Grüßen
Vorstand [Club-Name]
```

### Schritt 3: Vorstandsprüfung (Manual)
- • Vorstand bekommt Benachrichtigung (E-Mail/Dashboard)
- • Bewerber-Profil anschauen
- • Dokumente prüfen (Ausweis, Wohnsitz)
- • Zuverlässigkeitsprüfung (ggf. Anfrage)
- • Entscheidung: Annehmen / Ablehnen / Nachfragen

### Schritt 4a: Mitgliedschaft genehmigt
**System-Status:**
- • Mitgliedsstatus = "Genehmigt"
- • Mitgliedsnummer generieren (fortlaufend)
- • 6-Monats-Probezeit starten (Countdown)
- • Willkommens-E-Mail senden

**E-Mail an neues Mitglied:**
```
Betreff: Herzlich willkommen bei [Club-Name]! 🎉

Hallo [Name],

deine Mitgliedschaft wurde genehmigt!

Deine Mitgliedsnummer: [ID]
Mitglied seit: [Datum]
Probezeit: 6 Monate (bis [Datum])
Erster Cannabis-Zugang möglich ab: [Datum + 6 Monate]

Was du jetzt tun kannst:
- Mitgliedsausweis herunterladen
- Termin für Erstgespräch vereinbaren
- Club-Regeln durchlesen

Willkommen in der Community!

Mit freundlichen Grüßen
Vorstand [Club-Name]
```

### Schritt 4b: Mitgliedschaft abgelehnt
- • Mitgliedsstatus = "Abgelehnt"
- • Ablehnungs-E-Mail senden
- • Grund für Ablehnung (optional)
- • Daten nach 30 Tagen löschen (DSGVO)

### Schritt 4c: Nachfrage (Mehr Infos benötigt)
- • Status = "Warte auf Unterlagen"
- • E-Mail mit Anforderungen senden
- • Timer (z.B. 14 Tage für Antwort)
- • Automatische Erinnerung

---

## Limits & Warnungen

### Maximale Mitgliederzahl
- • **Hard Limit: 500 Mitglieder**
- • System blockiert neue Anmeldungen bei 500
- • Warteliste optional ermöglichen
- • Admin-Benachrichtigung bei 90% (450 Mitglieder)
- • Admin-Benachrichtigung bei 95% (475 Mitglieder)
- • Admin-Benachrichtigung bei 98% (490 Mitglieder)

### Warnungen für Vorstand
```
⚠️ Mitgliedslimit fast erreicht!
Aktuell: 485/500 Mitglieder (97%)

Optionen:
- Mitgliedschaftsbewerbungen pausieren
- Warteliste aktivieren
- Bestandsmitglieder aufräumen (Austritte)
```

---

## Mitgliedsstatus-Workflow

```
[Bewerbung eingegangen]
        ↓
[Warte auf Prüfung] ← Vorstand wird benachrichtigt
        ↓
    /        \
[Genehmigt]  [Abgelehnt]  [Mehr Infos]
     ↓            ↓              ↓
[Willkommen]  [Ablehnung]  [Warte auf Unterlagen]
     ↓            ↓              ↓
[Probezeit]   [Löschung]   [Prüfung erneut]
     ↓                          ↓
[Aktives Mitglied]      [Genehmigt/Abgelehnt]
```

### Status-Liste
- • **Bewerbung eingegangen** - Automatisch nach Formular-Submit
- • **Warte auf Prüfung** - Vorstand muss entscheiden
- • **Mehr Unterlagen nötig** - Nachforderung versendet
- • **Genehmigt** - Mitgliedschaft akzeptiert
- • **Abgelehnt** - Mitgliedschaft abgelehnt
- • **Probezeit** - 6 Monate vor erstem Zugang
- • **Aktiv** - Vollwertiges Mitglied (nach Probezeit)
- • **Gesperrt** - Temporär keine Abgaben möglich
- • **Austritt beantragt** - Kündigung eingereicht
- • **Austritt vollzogen** - Kein Zugriff mehr

---

## Automatische E-Mails

### 1. Bewerbung eingegangen
**Trigger:** Formular-Submit
**Empfänger:** Bewerber
**Inhalt:** Bestätigung, Bearbeitungszeit, nächste Schritte

### 2. Neue Bewerbung für Vorstand
**Trigger:** Formular-Submit
**Empfänger:** Vorstand (alle oder Ansprechpartner)
**Inhalt:** Zusammenfassung, Link zum Dashboard

### 3. Mitgliedschaft genehmigt
**Trigger:** Vorstand klickt "Genehmigen"
**Empfänger:** Neues Mitglied
**Inhalt:** Willkommen, Mitgliedsnummer, Probezeit-Info

### 4. Mitgliedschaft abgelehnt
**Trigger:** Vorstand klickt "Ablehnen"
**Empfänger:** Bewerber
**Inhalt:** Höfliche Ablehnung, ggf. Begründung

### 5. Unterlagen nachfordern
**Trigger:** Vorstand klickt "Nachfragen"
**Empfänger:** Bewerber
**Inhalt:** Liste fehlender Unterlagen, Deadline

### 6. Probezeit beendet
**Trigger:** 6 Monate nach Genehmigung
**Empfänger:** Mitglied
**Inhalt:** Erster Cannabis-Zugang jetzt möglich, wie geht es weiter?

### 7. Mitgliedslimit-Warnung
**Trigger:** 450/475/490 Mitglieder erreicht
**Empfänger:** Vorstand
**Inhalt:** Warnung, Handlungsoptionen

---

## Dashboard für Vorstand

### Übersicht Widgets
- • **Offene Bewerbungen:** 12 (warten auf Prüfung)
- • **Neue Mitglieder diesen Monat:** 5
- • **Mitglieder gesamt:** 423/500 (85%)
- • **Probezeit läuft:** 28 Mitglieder

### Bewerbungs-Tabelle
| Name | Datum | Status | Aktionen |
|------|-------|--------|----------|
| Max M. | 28.02. | Warte auf Prüfung | [Ansehen] [Genehmigen] [Ablehnen] |
| Lisa S. | 27.02. | Mehr Infos nötig | [Erinnerung senden] |

---

## Technische Umsetzung

### Datenbank-Modell
```python
class MembershipApplication(models.Model):
    status = models.CharField(choices=[...])
    applicant = models.ForeignKey(User)
    submitted_at = models.DateTimeField()
    reviewed_by = models.ForeignKey(Staff, null=True)
    reviewed_at = models.DateTimeField(null=True)
    rejection_reason = models.TextField(null=True)
    
class Member(models.Model):
    user = models.OneToOneField(User)
    member_number = models.CharField(unique=True)
    approved_at = models.DateTimeField()
    probation_until = models.DateField()  # 6 Monate
    status = models.CharField(choices=[...])
```

### E-Mail-Versand
- • Django E-Mail Backend
- • HTML + Plain Text Templates
- • Asynchron (Celery/Django-Q) - optional
- • BCC an Vorstand bei wichtigen Mails

---

## UI/UX Mockups (TODO)

*Hier sollten Wireframes/Designs für:*
- • Anmeldeformular
- • Vorstand-Dashboard (Bewerbungsübersicht)
- • Detail-Ansicht Bewerber
- • E-Mail-Vorlagen

*Werden nachgereicht*

---

## Offene Fragen

- [ ] Kann ein abgelehntes Mitglied sich erneut bewerben?
- [ ] Gibt es eine Wartezeit zwischen Ablehnung und Neubewerbung?
- [ ] Wie wird der Vorstand benachrichtigt? (E-Mail, Dashboard, App-Push?)
- [ ] Gibt es automatische Ablehnung bei roten Flaggen?
- [ ] Müssen Vorstände begründen wenn sie ablehnen?
- [ ] Kann ein Mitglied die Probezeit verkürzen? (aus medizinischen Gründen?)

---

**Verwandte Dokumente:**
- [96-gesetzliche-pflicht-features.md](./96-gesetzliche-pflicht-features.md) - 6-Monats-Probezeit, 500 Mitglieder-Limit
- [03-deutsches-csc-recht.md](./03-deutsches-csc-recht.md) - Rechtliche Grundlagen