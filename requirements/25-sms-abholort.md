# SMS-Benachrichtigungen & Auslieferungsstation

**Dokumentation:** Twilio SMS, Paket-Benachrichtigung, Abholorte

---

## SMS-Benachrichtigungssystem

### Anwendungsfälle

#### 1. Paket bereit zur Abholung
**Trigger:** Bestellung Status = "Bereit zur Abholung"

**SMS:**
```
Hallo [Vorname]! Deine Bestellung #[Nummer] ist bereit zur 
Abholung. Abholort: [Adresse]. Öffnungszeiten: Mo-Fr 15-19h.
Dein CSC Leipzig
```

#### 2. Mitgliedschaft genehmigt
**Trigger:** Vorstand genehmigt Antrag

**SMS:**
```
Herzlich willkommen im CSC Leipzig! Deine Mitgliedschaft 
wurde genehmigt. Mitgliedsnummer: [Nummer]. 
Prüfe deine E-Mails für weitere Infos.
```

#### 3. Erinnerung Arbeitsstunden
**Trigger:** Monatsende, fehlende Stunden

**SMS:**
```
Hallo [Vorname]! Du hast diesen Monat noch [X] Arbeitsstunden 
offen. Melde dich für Termine: [Link]
```

#### 4. Zahlung fehlgeschlagen
**Trigger:** Stripe Payment Failed

**SMS:**
```
Achtung: Deine Zahlung für [Monat] ist fehlgeschlagen. 
Bitte aktualisiere deine Zahlungsdaten: [Link]
```

---

## Technische Umsetzung

### Twilio Integration

```python
# settings.py
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_AUTH_TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_PHONE_NUMBER = '+491234567890'  # Deutsche Twilio-Nummer
```

```toml
# pyproject.toml
dependencies = [
    "twilio==8.0.0",
]
```

### SMS-Service

```python
from twilio.rest import Client
from django.conf import settings

class SMSService:
    """Service für SMS-Versand"""
    
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
    
    def send_sms(self, to_phone, message):
        """Sende SMS an Telefonnummer"""
        
        # Format: +49 123 456789 -> +49123456789
        formatted_phone = self._format_phone(to_phone)
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=formatted_phone
            )
            
            # In Datenbank loggen
            SMSLog.objects.create(
                phone_number=formatted_phone,
                message=message,
                twilio_sid=message.sid,
                status='sent'
            )
            
            return True, message.sid
            
        except Exception as e:
            # Fehler loggen
            SMSLog.objects.create(
                phone_number=formatted_phone,
                message=message,
                status='failed',
                error_message=str(e)
            )
            return False, str(e)
    
    def send_package_ready(self, member, order):
        """SMS: Paket bereit zur Abholung"""
        
        message = (
            f"Hallo {member.user.first_name}! "
            f"Deine Bestellung #{order.order_number} ist bereit zur Abholung. "
            f"Abholort: {order.pickup_location.name}, "
            f"{order.pickup_location.address}. "
            f"Öffnungszeiten: {order.pickup_location.opening_hours}. "
            f"Dein CSC Leipzig"
        )
        
        return self.send_sms(member.phone, message)
    
    def _format_phone(self, phone):
        """Formatiere Telefonnummer für Twilio"""
        # Entferne Leerzeichen und +
        phone = phone.replace(' ', '').replace('-', '')
        
        # Füge +49 hinzu wenn nicht vorhanden
        if phone.startswith('0'):
            phone = '+49' + phone[1:]
        elif not phone.startswith('+'):
            phone = '+' + phone
        
        return phone
```

### SMS-Log

```python
class SMSLog(models.Model):
    """Protokoll aller versendeten SMS"""
    
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True)
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    
    # Twilio
    twilio_sid = models.CharField(max_length=255)
    status = models.CharField(choices=[
        ('sent', 'Gesendet'),
        ('delivered', 'Zugestellt'),
        ('failed', 'Fehlgeschlagen'),
    ])
    
    # Zeit
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True)
    
    # Fehler
    error_message = models.TextField(blank=True)
```

---

## Auslieferungsstation (Abholort)

### Konzept
- Produktionsräume (Anbau) ≠ Auslieferungsstation (Abholung)
- Mehrere Abholorte möglich
- Mitglied wählt bevorzugten Abholort

### Modell

```python
class PickupLocation(models.Model):
    """Auslieferungsstation / Abholort"""
    
    name = models.CharField(max_length=255)  # "Hauptstelle Mitte"
    
    # Adresse
    street = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    
    # Kontakt
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Öffnungszeiten
    opening_hours = models.TextField()
    # z.B.: "Mo-Fr: 15:00-19:00, Sa: 10:00-14:00"
    
    # Beschreibung / Anfahrtsbeschreibung
    description = models.TextField(blank=True)
    
    # Google Maps Link
    maps_url = models.URLField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)  # Standard-Abholort
    
    # Reihenfolge
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.city})"
```

### Bestellung mit Abholort

```python
class Order(models.Model):
    """Erweiterung um Abholort"""
    
    # ... bestehende Felder ...
    
    # Abholort
    pickup_location = models.ForeignKey(
        PickupLocation, 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    # Abholstatus
    PICKUP_STATUS_CHOICES = [
        ('preparing', 'Wird vorbereitet'),
        ('ready', 'Bereit zur Abholung'),
        ('picked_up', 'Abgeholt'),
        ('reminder_sent', 'Erinnerung gesendet'),
    ]
    pickup_status = models.CharField(
        max_length=20, 
        choices=PICKUP_STATUS_CHOICES,
        default='preparing'
    )
    
    # Abholidatum
    ready_at = models.DateTimeField(null=True)
    picked_up_at = models.DateTimeField(null=True)
    picked_up_by = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True)
    
    # SMS-Benachrichtigung
    sms_sent_at = models.DateTimeField(null=True)
    sms_delivered = models.BooleanField(default=False)
```

### Admin: Abholorte verwalten

```
📍 Abholorte

┌─────────────────────────────────────────────┐
│ Hauptstelle Mitte                          │
│ Musterstraße 42, 12345 Leipzig             │
│ Tel: 0123-456789                           │
│ Öffnungszeiten: Mo-Fr 15-19h, Sa 10-14h   │
│ ✅ Standard-Abholort                        │
│ ✅ Aktiv                                    │
│ [Bearbeiten] [Deaktivieren]                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Filiale Nord                               │
│ Nordstraße 10, 12345 Leipzig               │
│ Tel: 0123-456790                           │
│ Öffnungszeiten: Mo-Do 16-20h              │
│ Standard: Nein                              │
│ ✅ Aktiv                                    │
│ [Bearbeiten] [Deaktivieren]                │
└─────────────────────────────────────────────┘

[+ Neuen Abholort hinzufügen]
```

### Checkout: Abholort wählen

```
🛒 Checkout

Schritt 3 von 4: Abholort wählen

Wo möchtest du deine Bestellung abholen?

┌─────────────────────────────────────────────┐
│ ○ Hauptstelle Mitte (Standard)             │
│   Musterstraße 42, 12345 Leipzig           │
│   Mo-Fr: 15-19h, Sa: 10-14h               │
│   📍 Google Maps                           │
├─────────────────────────────────────────────┤
│ ○ Filiale Nord                             │
│   Nordstraße 10, 12345 Leipzig             │
│   Mo-Do: 16-20h                           │
│   📍 Google Maps                           │
└─────────────────────────────────────────────┘

[Weiter zur Zahlung →]
```

### Workflow: Paket-Bereitschaft

```
1. Bestellung kommt rein
        ↓
2. Mitarbeiter packt Paket
        ↓
3. Status = "Bereit zur Abholung"
        ↓
4. System sendet SMS an Mitglied
        ↓
5. Mitglied holt ab
        ↓
6. Status = "Abgeholt"
        ↓
7. Nach 7 Tagen: Erinnerung wenn nicht abgeholt
```

### Automatische Erinnerung

```python
def send_pickup_reminders():
    """Täglicher Job: Erinnere an nicht abgeholte Pakete"""
    
    # Pakete die seit 7 Tagen bereit liegen
    old_orders = Order.objects.filter(
        pickup_status='ready',
        ready_at__lte=timezone.now() - timedelta(days=7),
        reminder_sent=False
    )
    
    for order in old_orders:
        # SMS senden
        sms_service.send_sms(
            order.member.phone,
            f"Hallo {order.member.user.first_name}! "
            f"Deine Bestellung #{order.order_number} wartet noch auf dich. "
            f"Bitte hole sie bald ab: {order.pickup_location.name}"
        )
        
        order.reminder_sent = True
        order.save()
```

---

## SMS-Vorlagen (Admin konfigurierbar)

```python
class SMSTemplate(models.Model):
    """Vorlagen für SMS-Nachrichten"""
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    # Template mit Platzhaltern
    template_text = models.TextField()
    # z.B.: "Hallo {{vorname}}! Deine Bestellung {{bestellnummer}} ist bereit."
    
    # Verfügbare Platzhalter
    available_placeholders = models.JSONField(default=list)
    
    is_active = models.BooleanField(default=True)
```

### Beispiel-Templates

| Template | Text |
|----------|------|
| paket_bereit | Hallo {{vorname}}! Deine Bestellung {{bestellnummer}} ist bereit zur Abholung. {{abholort}}. {{verein}} |
| willkommen | Herzlich willkommen im {{verein}}! Deine Mitgliedsnummer: {{mitgliedsnummer}}. |
| arbeitsstunden | Hallo {{vorname}}! Du hast noch {{fehlende_stunden}} Arbeitsstunden offen. |

---

## Kosten & Limits

### Twilio Preise (ca.)
- SMS Deutschland: ~€0.075 pro SMS
- 100 SMS/Monat: ~€7.50
- 1000 SMS/Monat: ~€75

### Limits
- Max 1 SMS pro Stunde pro Mitglied (Rate Limiting)
- Nur wichtige Benachrichtigungen (kein Spam)
- Opt-out möglich

---

**Verwandte Dokumente:**
- [18-zahlungs-system.md](./18-zahlungs-system.md) - Bestellungen
- [16-mitgliedschafts-workflow.md](./16-mitgliedschafts-workflow.md) - Telefonnummer