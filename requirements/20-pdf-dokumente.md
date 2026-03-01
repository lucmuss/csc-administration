# PDF-Dokumente & Mitgliedsausweis

**Dokumentation:** Automatische PDF-Generierung, Platzhalter-System, E-Mail-Versand

---

## Überblick

Mitglied erhält automatisch nach Genehmigung:
1. • Aufnahmeantrag (ausgefüllt mit seinen Daten)
2. • Satzung des Vereins
3. • Mitgliedsausweis (PDF)
4. • Weitere Dokumente (Beitragsordnung, etc.)

**Alles als PDF per E-Mail.**

---

## Admin: Template-Verwaltung

### Template-System

Admin kann Dokumente als Templates hochladen und verwalten:

```
📄 Dokument-Templates

┌─────────────────────────────────────────────┐
│ Aufnahmeantrag                              │
│ Status: ✅ Aktiv                            │
│ Format: HTML                                │
│ Letzte Änderung: 28.02.2026                │
│                                             │
│ [Bearbeiten] [Vorschau] [Deaktivieren]     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Mitgliedsausweis                            │
│ Status: ✅ Aktiv                            │
│ Format: HTML                                │
│ Letzte Änderung: 15.01.2026                │
│                                             │
│ [Bearbeiten] [Vorschau] [Deaktivieren]     │
└─────────────────────────────────────────────┘

[+ Neues Template hochladen]
```

### Template-Editor

```
Template bearbeiten: Aufnahmeantrag

Name: [Aufnahmeantrag________________________]

Platzhalter (werden automatisch ersetzt):
{{MITGLIEDSNUMMER}} - Mitgliedsnummer
{{VORNAME}} - Vorname
{{NACHNAME}} - Nachname
{{GEBURTSDATUM}} - Geburtsdatum
{{STRASSE}} - Straße
{{PLZ}} - Postleitzahl
{{ORT}} - Wohnort
{{EMAIL}} - E-Mail
{{TELEFON}} - Telefon
{{EINTRITTSDATUM}} - Eintrittsdatum
{{DATUM_HEUTE}} - Aktuelles Datum
{{VORSTAND_VORSITZ}} - Name Vorstandsvorsitz

HTML-Template:
[textarea mit HTML-Code]

[✅ Pflichtfelder prüfen]
[Vorschau mit Testdaten]
[Speichern]
```

### Pflicht-Validierung

**WICHTIG:** Dokument kann NUR generiert werden wenn ALLE Pflicht-Platzhalter im Mitglied-Datensatz vorhanden sind.

```python
class DocumentTemplate(models.Model):
    """Vorlage für PDF-Dokumente"""
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    
    # Template-Inhalt (HTML)
    html_content = models.TextField()
    
    # Erforderliche Platzhalter (JSON-Liste)
    required_placeholders = models.JSONField(default=list)
    # z.B.: ["{{VORNAME}}", "{{NACHNAME}}", "{{MITGLIEDSNUMMER}}"]
    
    # Optionale Platzhalter
    optional_placeholders = models.JSONField(default=list)
    
    is_active = models.BooleanField(default=True)
    
    def validate_member_data(self, member):
        """Prüft ob alle Pflichtdaten vorhanden"""
        missing = []
        
        for placeholder in self.required_placeholders:
            value = member.get_placeholder_value(placeholder)
            if not value or value.strip() == "":
                missing.append(placeholder)
        
        if missing:
            raise ValidationError(
                f"Dokument kann nicht generiert werden. "
                f"Fehlende Daten: {', '.join(missing)}"
            )
        
        return True

def generate_pdf_for_member(template, member):
    """PDF nur generieren wenn alle Daten vorhanden"""
    
    # 1. Validierung
    template.validate_member_data(member)
    
    # 2. Platzhalter ersetzen
    html = template.html_content
    for placeholder in template.required_placeholders + template.optional_placeholders:
        value = member.get_placeholder_value(placeholder)
        html = html.replace(placeholder, value or "")
    
    # 3. PDF generieren
    pdf = HTML(string=html).write_pdf()
    
    return pdf
```

### Fehlermeldung bei unvollständigen Daten

```
⚠️ Dokument kann nicht generiert werden

Folgende Pflichtangaben fehlen beim Mitglied:
• {{MITGLIEDSNUMMER}} - Mitglied hat noch keine Nummer
• {{AUSWEISNUMMER}} - Ausweisnummer nicht erfasst

Bitte vervollständigen Sie die Daten des Mitglieds:
[Daten vervollständigen →]
```

## PDF-Templates mit Platzhaltern

### Platzhalter-System
```python
# Beispiel-Platzhalter
{
    "{{MITGLIEDSNUMMER}}": "12345",
    "{{VORNAME}}": "Max",
    "{{NACHNAME}}": "Mustermann",
    "{{GEBURTSDATUM}}": "01.01.1990",
    "{{GEBURTSORT}}": "Leipzig",
    "{{STAATSANGEHOERIGKEIT}}": "Deutsch",
    "{{AUSWEISNUMMER}}": "PA123456",
    "{{STRASSE}}": "Musterstraße 123",
    "{{PLZ}}": "12345",
    "{{ORT}}": "Musterstadt",
    "{{EMAIL}}": "max@example.com",
    "{{TELEFON}}": "0123-456789",
    "{{HANDY}}": "0151-12345678",
    "{{EINTRITTSDATUM}}": "15.03.2026",
    "{{DATUM_HEUTE}}": "28.02.2026",
    "{{VORSTAND_VORSITZ}}": "Erika Musterfrau",
    "{{VEREINS_NAME}}": "CSC Leipzig e.V.",
    "{{VEREINS_ADRESSE}}": "Cannabisstraße 42, 12345 Leipzig",
}
```

### Dokument-Templates

#### 1. Aufnahmeantrag (PDF)
**Template:** `templates/pdf/aufnahmeantrag.html`
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .header { text-align: center; margin-bottom: 30px; }
        .field { margin-bottom: 15px; }
        .label { font-weight: bold; }
        .value { border-bottom: 1px solid #000; padding: 5px; }
        .signature { margin-top: 50px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Aufnahmeantrag</h1>
        <h2>{{VEREINS_NAME}}</h2>
    </div>
    
    <div class="field">
        <span class="label">Mitgliedsnummer:</span>
        <span class="value">{{MITGLIEDSNUMMER}}</span>
    </div>
    
    <div class="field">
        <span class="label">Name:</span>
        <span class="value">{{VORNAME}} {{NACHNAME}}</span>
    </div>
    
    <div class="field">
        <span class="label">Geburtsdatum:</span>
        <span class="value">{{GEBURTSDATUM}}</span>
    </div>
    
    <div class="field">
        <span class="label">Adresse:</span>
        <span class="value">{{STRASSE}}, {{PLZ}} {{ORT}}</span>
    </div>
    
    <div class="field">
        <span class="label">E-Mail:</span>
        <span class="value">{{EMAIL}}</span>
    </div>
    
    <div class="field">
        <span class="label">Telefon:</span>
        <span class="value">{{TELEFON}}</span>
    </div>
    
    <div class="field">
        <span class="label">Eintrittsdatum:</span>
        <span class="value">{{EINTRITTSDATUM}}</span>
    </div>
    
    <p style="margin-top: 30px;">
        Ich beantrage hiermit die Aufnahme in den {{VEREINS_NAME}}.
        Ich habe die Satzung gelesen und akzeptiere sie.
    </p>
    
    <div class="signature">
        <div style="float: left; width: 45%;">
            <div style="border-top: 1px solid #000; margin-top: 50px;">
                Ort, Datum
            </div>
        </div>
        <div style="float: right; width: 45%;">
            <div style="border-top: 1px solid #000; margin-top: 50px;">
                Unterschrift
            </div>
        </div>
    </div>
</body>
</html>
```

#### 2. Mitgliedsausweis (PDF)
**Design:** Scheckkarten-Format (85.60 × 53.98 mm)

**Vorderseite:**
```
┌─────────────────────────────────┐
│  🌿 {{VEREINS_NAME}}            │
│                                 │
│  ┌──────┐                       │
│  │ Foto │  {{VORNAME}}          │
│  │      │  {{NACHNAME}}         │
│  └──────┘                       │
│                                 │
│  Mitgliedsnummer:               │
│  {{MITGLIEDSNUMMER}}            │
│                                 │
│  Gültig bis: {{GUELTIG_BIS}}    │
│                                 │
│  [Barcode/QR-Code]              │
└─────────────────────────────────┘
```

**Rückseite:**
```
┌─────────────────────────────────┐
│  Kontakt:                       │
│  {{VEREINS_ADRESSE}}            │
│  {{VEREINS_EMAIL}}              │
│  {{VEREINS_TELEFON}}            │
│                                 │
│  Notfallkontakt:                │
│  {{NOTFALL_KONTAKT}}            │
│                                 │
│  ─────────────────────────────  │
│  Dieser Ausweis ist            │
│  Eigentum des Vereins.         │
│  Verlust bitte melden.         │
└─────────────────────────────────┘
```

**HTML-Template:**
```html
<!-- Mitgliedsausweis -->
<div style="width: 85.60mm; height: 53.98mm; border: 1px solid #000; padding: 10px; font-family: Arial;">
    <div style="text-align: center; border-bottom: 2px solid #2d5a27; padding-bottom: 5px;">
        <strong style="color: #2d5a27;">🌿 {{VEREINS_NAME}}</strong>
    </div>
    
    <div style="margin-top: 10px;">
        <div style="float: left; width: 30%;">
            <!-- Platzhalter für Foto -->
            <div style="width: 50px; height: 60px; border: 1px solid #ccc; background: #f0f0f0;">
                Foto
            </div>
        </div>
        <div style="float: right; width: 65%;">
            <strong>{{VORNAME}}</strong><br>
            <strong>{{NACHNAME}}</strong><br>
            <small>Mitgliedsnummer:</small><br>
            <strong>{{MITGLIEDSNUMMER}}</strong>
        </div>
    </div>
    
    <div style="clear: both; margin-top: 10px; text-align: center; font-size: 10px;">
        Gültig bis: {{GUELTIG_BIS}}<br>
        <img src="{{QR_CODE_URL}}" style="width: 40px; height: 40px;">
    </div>
</div>
```

#### 3. Satzung (PDF)
- • Statische PDF (keine Platzhalter nötig)
- • Oder: Vereinsspezifische Anpassungen

#### 4. Beitragsordnung (PDF)
- • Höhe der Mitgliedsbeiträge
- • Zahlungsmodalitäten
- • Fristen

---

## PDF-Generierung mit WeasyPrint

### Installation
```bash
# pyproject.toml
dependencies = [
    "weasyprint==60.1",
    "Pillow==10.2.0",
]
```

### Django Model
```python
class MemberDocument(models.Model):
    """Generierte Dokumente für Mitglieder"""
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    document_type = models.CharField(choices=[
        ('application', 'Aufnahmeantrag'),
        ('member_card', 'Mitgliedsausweis'),
        ('statute', 'Satzung'),
        ('fee_regulation', 'Beitragsordnung'),
    ])
    
    pdf_file = models.FileField(upload_to='member_documents/%Y/%m/')
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # E-Mail Versand
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
```

### PDF-Service
```python
from weasyprint import HTML
from django.template.loader import render_to_string
from django.core.files.base import ContentFile

class PDFService:
    """Service für PDF-Generierung"""
    
    @staticmethod
    def generate_application_form(member):
        """Generiere ausgefüllten Aufnahmeantrag"""
        
        # Platzhalter-Daten
        context = {
            'MITGLIEDSNUMMER': member.member_number,
            'VORNAME': member.user.first_name,
            'NACHNAME': member.user.last_name,
            'GEBURTSDATUM': member.birth_date.strftime('%d.%m.%Y'),
            'STRASSE': member.street,
            'PLZ': member.postal_code,
            'ORT': member.city,
            'EMAIL': member.user.email,
            'TELEFON': member.phone,
            'EINTRITTSDATUM': member.approved_at.strftime('%d.%m.%Y'),
            'DATUM_HEUTE': timezone.now().strftime('%d.%m.%Y'),
            'VEREINS_NAME': settings.CLUB_NAME,
            'VEREINS_ADRESSE': settings.CLUB_ADDRESS,
        }
        
        # HTML rendern
        html_string = render_to_string('pdf/aufnahmeantrag.html', context)
        
        # PDF generieren
        pdf_file = HTML(string=html_string).write_pdf()
        
        # Speichern
        filename = f"aufnahmeantrag_{member.member_number}.pdf"
        document = MemberDocument.objects.create(
            member=member,
            document_type='application',
            pdf_file=ContentFile(pdf_file, filename),
            generated_by=system_user
        )
        
        return document
    
    @staticmethod
    def generate_member_card(member):
        """Generiere Mitgliedsausweis"""
        
        # QR-Code generieren (für Verifizierung)
        qr_code = generate_qr_code(member.member_number)
        
        context = {
            'VORNAME': member.user.first_name,
            'NACHNAME': member.user.last_name,
            'MITGLIEDSNUMMER': member.member_number,
            'GUELTIG_BIS': member.membership_end_date.strftime('%d.%m.%Y') if member.membership_end_date else 'unbegrenzt',
            'VEREINS_NAME': settings.CLUB_NAME,
            'VEREINS_ADRESSE': settings.CLUB_ADDRESS,
            'VEREINS_EMAIL': settings.CLUB_EMAIL,
            'VEREINS_TELEFON': settings.CLUB_PHONE,
            'QR_CODE_URL': qr_code.url,
        }
        
        html_string = render_to_string('pdf/member_card.html', context)
        pdf_file = HTML(string=html_string).write_pdf()
        
        filename = f"mitgliedsausweis_{member.member_number}.pdf"
        document = MemberDocument.objects.objects.create(
            member=member,
            document_type='member_card',
            pdf_file=ContentFile(pdf_file, filename),
            generated_by=system_user
        )
        
        return document
```

---

## Automatischer E-Mail-Versand

### Trigger: Mitgliedschaft genehmigt
```python
def on_member_approved(member):
    """Wird aufgerufen wenn Vorstand Mitglied genehmigt"""
    
    # 1. PDFs generieren
    application_pdf = PDFService.generate_application_form(member)
    member_card_pdf = PDFService.generate_member_card(member)
    
    # 2. Statische Dokumente anhängen
    statute_pdf = settings.STATUTE_PDF_PATH
    fee_regulation_pdf = settings.FEE_REGULATION_PDF_PATH
    
    # 3. E-Mail senden
    send_welcome_email_with_docs(
        member=member,
        attachments=[
            application_pdf.pdf_file,
            member_card_pdf.pdf_file,
            statute_pdf,
            fee_regulation_pdf,
        ]
    )
```

### E-Mail-Template
```
Betreff: Willkommen! Deine Mitgliedsunterlagen

Hallo {{VORNAME}},

herzlich willkommen im {{VEREINS_NAME}}!

Deine Mitgliedschaft wurde genehmigt. Deine Mitgliedsnummer: {{MITGLIEDSNUMMER}}

Im Anhang findest du:
✓ Ausgefüllten Aufnahmeantrag
✓ Deinen Mitgliedsausweis (bitte ausdrucken)
✓ Unsere Satzung
✓ Die Beitragsordnung

Bitte drucke den Aufnahmeantrag aus, unterschreibe ihn und bringe ihn bei deiner ersten Abholung mit.

Dein Mitgliedsausweis ist bei jeder Abholung vorzuzeigen.

Nächste Schritte:
1. Dokumente ausdrucken
2. Aufnahmeantrag unterschreiben
3. Termin für erste Abholung vereinbaren (nach 6 Monaten Probezeit)

Bei Fragen erreichst du uns unter {{VEREINS_EMAIL}}.

Herzlich willkommen in der Community!

Dein Vorstand
{{VEREINS_NAME}}
```

---

## Admin: Dokumente verwalten

### Dokumente pro Mitglied
```
Mitglied: #12345 - Max Mustermann

┌─────────────────────────────────────┐
│ Generierte Dokumente               │
├─────────────────────────────────────┤
│ 📄 Aufnahmeantrag                  │
│    Generiert: 28.02.2026 14:30     │
│    [Download] [Neu generieren]     │
├─────────────────────────────────────┤
│ 🎫 Mitgliedsausweis                │
│    Generiert: 28.02.2026 14:30     │
│    [Download] [Neu generieren]     │
├─────────────────────────────────────┤
│ 📋 Satzung (statisch)              │
│    [Download]                      │
├─────────────────────────────────────┤
│ 📋 Beitragsordnung (statisch)      │
│    [Download]                      │
└─────────────────────────────────────┘

[Alle Dokumente per E-Mail senden]
```

---

## Statische Dokumente hochladen

### Admin-Interface
```
Globale Dokumente

Satzung:
[Aktuelle Datei: satzung.pdf]
[Neue Datei hochladen]

Beitragsordnung:
[Aktuelle Datei: beitragsordnung.pdf]
[Neue Datei hochladen]

Info-Broschüre:
[Aktuelle Datei: info.pdf]
[Neue Datei hochladen]
```

---

## Technische Umsetzung

### Dependencies
```toml
[project]
dependencies = [
    "weasyprint==60.1",      # PDF-Generierung
    "Pillow==10.2.0",        # Bildverarbeitung (Fotos)
    "qrcode==7.4.2",         # QR-Codes für Ausweis
]
```

### Dateiablage
```
media/
├── member_documents/
│   └── 2026/
│       └── 02/
│           ├── aufnahmeantrag_12345.pdf
│           ├── mitgliedsausweis_12345.pdf
│           └── ...
├── static_documents/
│   ├── satzung.pdf
│   ├── beitragsordnung.pdf
│   └── info_broschuere.pdf
└── member_photos/
    └── 12345.jpg
```

---

## UI-Mockups (TODO)

- • Dokumenten-Liste (Mitglied)
- • Dokumenten-Verwaltung (Admin)
- • PDF-Vorschau
- • Upload-Interface für statische Dokumente

---

**Warte auf Beispiele vom User:**
- [ ] Muster-Aufnahmeantrag
- [ ] Muster-Satzung
- [ ] Mitgliedsausweis-Design
- [ ] Weitere Dokumente

---

**Verwandte Dokumente:**
- [16-mitgliedschafts-workflow.md](./16-mitgliedschafts-workflow.md) - Genehmigungs-Prozess
- [11-tech-stack.md](./11-tech-stack.md) - WeasyPrint Dependency