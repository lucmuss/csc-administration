# Zahlungs-System & Checkout

**Dokumentation:** Stripe-Integration, Produkt-Katalog, Bestellprozess

---

## Unterschied zu RedFlag Analyzer

| RedFlag | CSC-Admin |
|---------|-----------|
| Credits-System (€20 = X Credits) | ❌ Keine Credits |
| Analysen für Credits kaufen | ❌ Direkte Produkt-Zahlung |
| Einheitlicher Preis | ✅ Preis pro Sorte unterschiedlich |
| Einfacher Checkout | ✅ Chargen-spezifische Bestellung |

---

## Zahlungs-Modell für CSC

### Grundprinzip: Spenden für Kostendeckung
- • **Kein Verkauf!** (wäre illegal)
• Mitglied "spendet" für Kosten des Clubs
• Gegenleistung: Cannabis zum Eigenkonsum
• Preis = Kostendeckung (nicht Gewinnorientiert)

### Preisgestaltung
- • Pro Sorte unterschiedliche Spenden-Empfehlung
- • Preis pro Gramm (z.B. €8-12/g je nach Sorte)
- • Keine Mengenrabatte (verboten? prüfen!)
- • Transparente Kalkulation

---

## Aufnahmegebühr (Einmalig)

### Mitgliedschafts-Aufnahme
- • Einmalige Aufnahmegebühr: €20 (Beispiel)
- • Deckt Verwaltungskosten
- • Bezahlung bei Registrierung
- • Alternativ: Mit erster Bestellung

### Stripe-Integration
```python
# Stripe Product: Aufnahmegebühr
stripe.Product.create(
    name="CSC Mitgliedschafts-Aufnahme",
    description="Einmalige Aufnahmegebühr",
)

stripe.Price.create(
    product=product.id,
    unit_amount=2000,  # €20.00
    currency="eur",
)
```

---

## Produkt-Katalog (Sorten)

### Sorte als Stripe-Produkt
```python
# Für jede Charge wird automatisch ein Stripe-Produkt erstellt
stripe.Product.create(
    name="Orange Bud - Charge #240301-OB",
    description="THC: 18%, CBD: 0.5%, Anbau: März 2024",
    metadata={
        "strain": "Orange Bud",
        "charge_id": "240301-OB",
        "thc_content": "18%",
        "cbd_content": "0.5%",
        "harvest_date": "2024-03-01",
        "available_grams": "3000",
    }
)

stripe.Price.create(
    product=product.id,
    unit_amount=1000,  # €10.00 pro Gramm
    currency="eur",
)
```

### Chargen-Verwaltung
- • Neue Charge einbuchen → Automatisch Stripe-Produkt anlegen
- • Verfügbare Menge tracken
- • Preis pro Gramm definieren
- • Produkt-Metadaten für Rückverfolgbarkeit

---

## Bestellprozess (User Journey)

### Schritt 1: Produkt-Übersicht (Shop-Seite)

**Kachel-Layout:**
```
┌─────────────────────────┐
│ 🌿 Orange Bud           │
│ Charge #240301-OB       │
│                         │
│ THC: 18% | CBD: 0.5%   │
│ Verfügbar: 2.847g      │
│                         │
│ 💰 €10.00 / Gramm      │
│                         │
│ Menge: [1-25 ▼] Gramm  │
│                         │
│ [🛒 In den Warenkorb]  │
└─────────────────────────┘

┌─────────────────────────┐
│ 🌿 Blue Dream           │
│ Charge #240228-BD       │
│                         │
│ THC: 20% | CBD: 0.3%   │
│ Verfügbar: 1.523g      │
│                         │
│ 💰 €12.00 / Gramm      │
│                         │
│ [AUSVERKAUFT]          │
└─────────────────────────┘
```

**Features:**
- • Sorten-Kacheln mit Bild
- • THC/CBD Gehalt anzeigen
- • Verfügbare Menge (live)
- • Dropdown: 1g, 2g, 3g, 5g, 10g, 25g (max)
- • In den Warenkorb
- • Filtern nach THC-Gehalt, Preis

### Schritt 2: Warenkorb

```
🛒 Warenkorb

┌────────────────────────────────┐
│ Orange Bud - Charge #240301-OB │
│ 5 Gramm × €10.00 = €50.00     │
│ [🗑️]                          │
├────────────────────────────────┤
│ Blue Dream - Charge #240228-BD │
│ 3 Gramm × €12.00 = €36.00     │
│ [🗑️]                          │
├────────────────────────────────┤
│ Zwischensumme:     €86.00     │
│ Aufnahmegebühr:    €20.00     │
│                                  │
│ Gesamtsumme:       €106.00    │
│                                  │
│ [Zur Kasse →]                  │
└────────────────────────────────┘
```

**Validierungen:**
- • Tageslimit prüfen (max 25g)
- • Monatslimit prüfen (max 50g)
- • Chargen-Verfügbarkeit prüfen
- • Mitgliedschaft aktiv?
- • Probezeit abgeschlossen?

### Schritt 3: Checkout

**Bestellübersicht:**
```
📋 Bestellung abschließen

Produkte:
• Orange Bud (5g) - Charge #240301-OB ..... €50.00
• Blue Dream (3g) - Charge #240228-BD ..... €36.00

Aufnahmegebühr (einmalig) .................. €20.00

Gesamtsumme ............................... €106.00

💳 Zahlung mit:
[💳 Kreditkarte] [🏦 SEPA-Lastschrift] [💰 PayPal]

[Jetzt spenden & bestellen]
```

**Stripe Checkout:**
- • Embedded Checkout oder Redirect
- • SCA-konform (3D Secure)
- • SEPA-Lastschrift optional
- • Rechnungskauf? (prüfen!)

### Schritt 4: Bestätigung

**Nach erfolgreicher Zahlung:**
```
✅ Vielen Dank für deine Unterstützung!

Bestellnummer: #12345

Deine Bestellung:
• Orange Bud (5g) - Charge #240301-OB
• Blue Dream (3g) - Charge #240228-BD

Gesamtsumme gespendet: €106.00

📧 Eine Bestätigung wurde an deine E-Mail gesendet.

Abholung:
Deine Bestellung ist bereit zur Abholung.
Bitte bringe deinen Ausweis und Mitgliedsausweis mit.

[Nächste Schritte →]
```

---

## Stripe-Implementation

### Django Models

```python
class Product(models.Model):
    """Cannabis Sorte / Charge"""
    name = models.CharField(max_length=255)  # "Orange Bud"
    charge_number = models.CharField(max_length=50)  # "240301-OB"
    thc_content = models.DecimalField(max_digits=4, decimal_places=2)
    cbd_content = models.DecimalField(max_digits=4, decimal_places=2)
    price_per_gram = models.DecimalField(max_digits=6, decimal_places=2)
    available_grams = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Stripe IDs
    stripe_product_id = models.CharField(max_length=255)
    stripe_price_id = models.CharField(max_length=255)
    
    is_active = models.BooleanField(default=True)

class Order(models.Model):
    """Bestellung eines Mitglieds"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=50, unique=True)
    
    # Stripe
    stripe_checkout_session_id = models.CharField(max_length=255)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True)
    
    # Beträge
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_membership_fee_included = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(choices=[
        ('pending', 'Ausstehend'),
        ('paid', 'Bezahlt'),
        ('ready', 'Bereit zur Abholung'),
        ('dispensed', 'Ausgegeben'),
        ('cancelled', 'Storniert'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    """Einzelne Position in Bestellung"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_grams = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_gram = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Chargen-Rückverfolgbarkeit
    charge_batch_number = models.CharField(max_length=50)
```

### Stripe Webhook

```python
@csrf_exempt
def stripe_webhook(request):
    """Stripe sendet Events bei Zahlungen"""
    
    event = stripe.Webhook.construct_event(
        payload, sig_header, endpoint_secret
    )
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Bestellung als bezahlt markieren
        order = Order.objects.get(
            stripe_checkout_session_id=session.id
        )
        order.status = 'paid'
        order.stripe_payment_intent_id = session.payment_intent
        order.save()
        
        # E-Mail an Mitglied senden
        send_order_confirmation_email(order)
        
        # Vorstand benachrichtigen
        notify_staff_new_order(order)
```

---

## Chargen-Rückverfolgbarkeit in Bestellung

### Jedes Produkt verknüpft mit Charge
```
Bestellung #12345
├─ Orange Bud 5g
│  └─ Charge #240301-OB
│     ├─ Anbau-Datum: 01.03.2024
│     ├─ Ernte-Datum: 15.04.2024
│     ├─ THC: 18%
│     └─ Verantwortlich: Max Mustermann
│
└─ Blue Dream 3g
   └─ Charge #240228-BD
      ├─ Anbau-Datum: 28.02.2024
      ├─ Ernte-Datum: 10.04.2024
      └─ THC: 20%
```

### Export für Behörden
```
Mitglied: #123 - Max Mustermann
Datum: 28.02.2026

Abgabe:
- Orange Bud 5g (Charge #240301-OB, THC 18%)
- Blue Dream 3g (Charge #240228-BD, THC 20%)

Herkunft jeder Charge dokumentiert.
Nachweis: Anbau-Protokolle vorhanden.
```

---

## Admin: Chargen einbuchen

### Workflow für Vorstand

```
1. Neue Charge einbuchen
   ├─ Sorte: Orange Bud
   ├─ Menge: 3000g
   ├─ THC: 18%
   ├─ CBD: 0.5%
   ├─ Anbau-Datum: 01.03.2024
   ├─ Ernte-Datum: 15.04.2024
   └─ Preis/Gramm: €10.00

2. System legt automatisch an:
   ├─ Charge-ID: 240301-OB
   ├─ Stripe Product
   ├─ Stripe Price
   └─ Im Shop verfügbar

3. Mitglied kann bestellen
```

---

## Offene Fragen / Rechtliches

- [ ] Sind Mengenrabatte erlaubt? (5g = €9/g, 10g = €8/g?)
- [ ] Mindestbestellmenge erlaubt?
- [ ] Maximalbetrag pro Bestellung?
- [ ] SEPA-Lastschrift für CSC erlaubt?
- [ ] Rechnungskauf möglich?
- [ ] Ratenzahlung? (bestimmt nicht)
- [ ] Gutscheine/Guthaben erlaubt?

**→ Rechtsanwalt fragen vor Implementation!**

---

## UI-Mockups (TODO)

- • Shop-Seite mit Kacheln
- • Warenkorb
- • Checkout-Formular
- • Bestellhistorie (Mitglied)
- • Chargen-Verwaltung (Admin)

---

**Verwandte Dokumente:**
- [11-tech-stack.md](./11-tech-stack.md) - Stripe Dependency
- [96-gesetzliche-pflicht-features.md](./96-gesetzliche-pflicht-features.md) - Chargen-Rückverfolgung
- [16-mitgliedschafts-workflow.md](./16-mitgliedschafts-workflow.md) - Aufnahmegebühr