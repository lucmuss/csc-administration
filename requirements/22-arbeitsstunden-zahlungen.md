# Arbeitsstunden, Guthaben & Automatische Zahlungen

**Dokumentation:** Mitgliedsbeiträge, Arbeitszeit, Stripe-Abgleich

---

## Übersicht: Zwei Finanz-Ströme

### 1. Regelmäßige Mitgliedsbeiträge
- • **24€/Monat** (Beispiel)
- • Automatisch per Stripe einziehen
- • Verwendungszweck: Mitglieds-ID
- • Prüfung auf Zahlungseingang

### 2. Ausschank-Zahlungen (Spenden)
- • Produkte bestellen → Stripe-Checkout
- • Einmalige Zahlungen
- • Sofortige Buchung

---

## 1. Arbeitsstunden-System (Guthabenkonto)

### Konzept
Mitglieder müssen **monatlich Zeit** im Club einbringen:
- • Beispiel: 4 Stunden/Monat
- • Oder: Variable je nach Vereinssatzung
- • Nicht geleistet → Konversion in Geld oder Ausschluss

### Arbeitsstunden-Tracking

```python
class WorkHours(models.Model):
    """Geleistete Arbeitsstunden eines Mitglieds"""
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    date = models.DateField()
    hours = models.DecimalField(max_digits=4, decimal_places=2)  # z.B. 2.5 Stunden
    
    # Was wurde gemacht?
    activity = models.CharField(max_length=255)  # "Gießen", "Ernte", "Putzen"
    
    # Wer hat bestätigt?
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    confirmed_at = models.DateTimeField(auto_now_add=True)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('confirmed', 'Bestätigt'),
        ('rejected', 'Abgelehnt'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    notes = models.TextField(blank=True)

class WorkHoursQuota(models.Model):
    """Soll-Arbeitsstunden pro Monat"""
    
    # Global oder pro Mitglied konfigurierbar
    required_hours_per_month = models.DecimalField(max_digits=4, decimal_places=2, default=4.0)
    
    # Alternativ: Geldwert bei Nichterfüllung
    conversion_rate_per_hour = models.DecimalField(max_digits=6, decimal_places=2, default=15.00)  # €15/Stunde
```

### Arbeitsstunden-Übersicht (Dashboard)

```
Mitglied: #12345 - Max Mustermann

┌────────────────────────────────────────┐
│ Arbeitsstunden März 2026              │
├────────────────────────────────────────┤
│ Soll:        4.0 Stunden              │
│ Ist:         2.5 Stunden              │
│ Offen:       1.5 Stunden              │
│ Status:      ⚠️ Nicht erfüllt         │
├────────────────────────────────────────┤
│ Geleistet:                            │
│ • 15.03. - Gießen (2h) ✓ bestätigt   │
│ • 20.03. - Ernte (0.5h) ✓ bestätigt  │
└────────────────────────────────────────┘

[Arbeitsstunden eintragen]
```

### Konversion bei Nichterfüllung

```python
def check_work_hours_at_month_end():
    """Prüfung am Monatsende"""
    
    for member in Member.objects.active():
        required = member.work_hours_quota.required_hours_per_month
        actual = member.get_work_hours_this_month()
        
        if actual < required:
            missing = required - actual
            conversion_rate = member.work_hours_quota.conversion_rate_per_hour
            amount = missing * conversion_rate
            
            # Automatisch als Zusatzzahlung buchen
            create_additional_payment(member, amount, reason=f"Fehlende Arbeitsstunden: {missing}h")
```

### Admin: Arbeitsstunden bestätigen

```
Ausstehende Arbeitsstunden (3)

┌──────────┬──────────┬──────────┬─────────┬──────────┐
│ Mitglied │ Datum    │ Stunden  │ Tätigkeit│ Aktionen │
├──────────┼──────────┼──────────┼─────────┼──────────┤
│ #12345   │ 25.03.   │ 3.0h     │ Putzen  │ [✓] [✗] │
│ #12346   │ 26.03.   │ 2.0h     │ Gießen  │ [✓] [✗] │
│ #12347   │ 26.03.   │ 4.0h     │ Ernte   │ [✓] [✗] │
└──────────┴──────────┴──────────┴─────────┴──────────┘
```

---

## 2. Automatische Mitgliedsbeiträge (24€/Monat)

### Stripe Setup

#### Stripe Connect
- • Club-Konto (IBAN) bei Stripe hinterlegen
- • Stripe übernimmt Einzug
- • Automatische Zuordnung via Verwendungszweck

#### Stripe Produkte

```python
# Einmalig: Stripe-Produkt für Mitgliedsbeitrag erstellen
stripe.Product.create(
    name="CSC Mitgliedsbeitrag",
    description="Monatlicher Mitgliedsbeitrag",
)

stripe.Price.create(
    product=product.id,
    unit_amount=2400,  # €24.00
    currency="eur",
    recurring={"interval": "month"},  # Monatlich!
)
```

### Mitglied-Modell Erweiterung

```python
class Member(models.Model):
    # ... bestehende Felder ...
    
    # Stripe für wiederkehrende Zahlungen
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    
    # Zahlungsstatus
    PAYMENT_STATUS_CHOICES = [
        ('active', 'Aktiv'),
        ('past_due', 'Überfällig'),
        ('canceled', 'Gekündigt'),
        ('unpaid', 'Unbezahlt'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='active')
    
    # Verwendungszweck für Überweisungen
    payment_reference = models.CharField(max_length=50, unique=True)  # z.B. "CSC-12345"
    
    # Zahlungshistorie
    last_payment_date = models.DateField(null=True, blank=True)
    last_payment_amount = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
```

### Automatischer Einzug

#### Variante A: Stripe Subscription (empfohlen)
```python
def setup_stripe_subscription(member):
    """Richte monatliche Abbuchung ein"""
    
    # Stripe Customer erstellen
    customer = stripe.Customer.create(
        email=member.user.email,
        name=f"{member.user.first_name} {member.user.last_name}",
        metadata={"member_id": member.member_number},
    )
    
    # Zahlungsmethode hinzufügen (Mandat)
    # Mitglied muss Zahlungsdaten einmalig eingeben
    
    # Subscription erstellen
    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[{"price": "price_1Mitgliedsbeitrag24Euro"}],
        metadata={"member_id": member.member_number},
    )
    
    member.stripe_customer_id = customer.id
    member.stripe_subscription_id = subscription.id
    member.save()
```

#### Variante B: SEPA-Lastschrift
```python
def setup_sepa_direct_debit(member):
    """SEPA-Lastschrift einrichten"""
    
    # Mitglied gibt IBAN ein
    # Stripe erstellt Mandat
    # Monatliche Lastschrift
    
    payment_method = stripe.PaymentMethod.create(
        type="sepa_debit",
        sepa_debit={"iban": member.iban},
        billing_details={
            "name": member.user.get_full_name(),
            "email": member.user.email,
        },
    )
    
    # Mandat bestätigen
    # ...
```

### Zahlungsabgleich (Automatisch)

#### Stripe Webhook
```python
@csrf_exempt
def stripe_webhook(request):
    """Stripe sendet Events"""
    
    event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    
    if event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        member = Member.objects.get(stripe_customer_id=invoice.customer)
        
        # Zahlung verbuchen
        MembershipPayment.objects.create(
            member=member,
            amount=invoice.amount_paid / 100,  # Cent zu Euro
            stripe_invoice_id=invoice.id,
            payment_date=timezone.now(),
            status='completed',
        )
        
        # Mitglied aktualisieren
        member.last_payment_date = timezone.now()
        member.last_payment_amount = invoice.amount_paid / 100
        member.payment_status = 'active'
        member.save()
        
        # E-Mail-Bestätigung
        send_payment_confirmation(member, invoice.amount_paid / 100)
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        member = Member.objects.get(stripe_customer_id=invoice.customer)
        
        # Status ändern
        member.payment_status = 'past_due'
        member.save()
        
        # Mahnung senden
        send_payment_reminder(member)
```

### Zahlungs-Tracking

```python
class MembershipPayment(models.Model):
    """Einzelne Mitgliedsbeitrags-Zahlung"""
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=6, decimal_places=2)  # €24.00
    
    # Referenz
    payment_reference = models.CharField(max_length=50)  # z.B. "CSC-12345-MAR2026"
    
    # Stripe
    stripe_invoice_id = models.CharField(max_length=255, blank=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('completed', 'Abgeschlossen'),
        ('failed', 'Fehlgeschlagen'),
        ('refunded', 'Zurückerstattet'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Zeiten
    payment_date = models.DateField()
    period_start = models.DateField()  # Für welchen Monat?
    period_end = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 3. Verwendungszweck = Mitglieds-ID

### Bei Überweisungen
```
Empfänger: CSC Leipzig e.V.
IBAN: DE12 3456 7890 1234 5678 90

Verwendungszweck: CSC-12345
                    ^^^^^^^^^^
                    Mitgliedsnummer
```

### Automatische Zuordnung
```python
def process_bank_statement():
    """Täglicher Job: Abgleich mit Bank"""
    
    # Stripe Bank Account API oder CSV-Import
    transactions = get_stripe_bank_transactions()
    
    for tx in transactions:
        # Extrahiere Mitgliedsnummer aus Verwendungszweck
        match = re.search(r'CSC-(\d+)', tx.description)
        if match:
            member_number = match.group(1)
            member = Member.objects.get(member_number=member_number)
            
            # Zahlung zuordnen
            MembershipPayment.objects.create(
                member=member,
                amount=tx.amount,
                payment_reference=tx.description,
                status='completed',
                payment_date=tx.date,
            )
```

---

## 4. Admin: Zahlungsübersicht

### Dashboard
```
Zahlungen März 2026

┌────────────────────────────────────────┐
│ Übersicht                             │
├────────────────────────────────────────┤
│ Erwartet:      342 × €24 = €8.208    │
│ Eingegangen:   €7.920 (96%)           │
│ Offen:         €288 (4%)              │
│ Fehlgeschlagen: €120 (2 Fälle)       │
└────────────────────────────────────────┘

⚠️ Überfällige Zahlungen (2)
• #12345 - Max M. - seit 15.03.
• #12346 - Lisa S. - seit 20.03.
```

### Mitglieder-Liste mit Zahlungsstatus
```
┌──────────┬─────────────┬────────────┬──────────┬──────────┐
│ Mitglied │ Name        │ Letzte Zahl│ Status   │ Aktion   │
├──────────┼─────────────┼────────────┼──────────┼──────────┤
│ #12345   │ Max M.      │ 15.02.     │ ⚠️ Offen │ [Mahnen] │
│ #12346   │ Lisa S.     │ 01.03.     │ ✅ OK    │          │
│ #12347   │ Tom B.      │ 01.03.     │ ✅ OK    │          │
└──────────┴─────────────┴────────────┴──────────┴──────────┘
```

---

## 5. Automatisierte Jobs (Cron)

### Täglich
```python
# jobs/daily.py

def check_payment_status():
    """Prüfe Zahlungseingänge"""
    # Stripe API abfragen
    # Offene Zahlungen identifizieren
    pass

def send_payment_reminders():
    """Sende Zahlungserinnerungen"""
    # Mitglieder mit offenen Zahlungen (>7 Tage)
    pass
```

### Monatlich
```python
# jobs/monthly.py

def check_work_hours():
    """Prüfe Arbeitsstunden Vormonat"""
    # Wer hat nicht genug Stunden?
    # Konversion in Geld
    pass

def generate_payment_report():
    """Finanzbericht für Vorstand"""
    pass
```

---

## 6. E-Mail-Kommunikation

### Zahlung erfolgreich
```
Betreff: Zahlungseingang bestätigt - März 2026

Hallo [Vorname],

wir haben deinen Mitgliedsbeitrag für März 2026 erhalten.

Betrag: €24.00
Datum: 01.03.2026
Referenz: CSC-12345-MAR2026

Vielen Dank!

Dein Vorstand
```

### Zahlung fehlgeschlagen
```
Betreff: Zahlung fehlgeschlagen - bitte aktualisiere deine Daten

Hallo [Vorname],

leider konnte dein Mitgliedsbeitrag für März 2026 nicht eingezogen werden.

Grund: [Grund von Stripe]

Bitte aktualisiere deine Zahlungsdaten:
[Zahlungsdaten aktualisieren →]

Bei wiederholtem Fehlschlagen wird deine Mitgliedschaft vorübergehend gesperrt.
```

### Mahnung Arbeitsstunden
```
Betreff: Fehlende Arbeitsstunden März 2026

Hallo [Vorname],

du hast im März nur 2 von 4 erforderlichen Arbeitsstunden geleistet.

Fehlend: 2 Stunden
Konversion: €30.00 (2h × €15)

Dieser Betrag wird mit deiner nächsten Zahlung eingezogen.

Oder: Melde dich für Arbeitsstunden an:
[Termin vereinbaren →]
```

---

## Technische Umsetzung

### Dependencies
```toml
[project]
dependencies = [
    "stripe==14.3.0",
    "django-celery-beat==2.5.0",  # Für Cron-Jobs
    "django-celery-results==2.5.0",
]
```

### ⚠️ Wichtig: Kein Celery!
Da **PostgreSQL-Only Rule** gilt:
- ❌ Kein Redis für Celery
- ✅ Alternative: django-background-tasks
- ✅ Oder: django-q mit PostgreSQL-Backend
- ✅ Oder: Einfache Cron-Jobs via django-crontab

### Empfohlene Lösung (PostgreSQL-only)
```toml
django-background-tasks==1.2.5
```

---

## Zusammenfassung

| Feature | Umsetzung |
|---------|-----------|
| Arbeitsstunden | Model + Bestätigung + Konversion |
| Autom. Beiträge | Stripe Subscription (24€/Monat) |
| Verwendungszweck | CSC-[Mitgliedsnummer] |
| Abgleich | Stripe Webhook + täglicher Job |
| Jobs | django-background-tasks (kein Redis!) |

---

**Verwandte Dokumente:**
- [18-zahlungs-system.md](./18-zahlungs-system.md) - Stripe Checkout für Ausschank
- [19-warenwirtschaft.md](./19-warenwirtschaft.md) - Mitglieder-Model
- [11-tech-stack.md](./11-tech-stack.md) - PostgreSQL-Only Constraint