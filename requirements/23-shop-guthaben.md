# Startseite, Shop-System & Guthaben

**Dokumentation:** Landing Page, Mitglieder-Shop, Guthaben-System, Limits

---

## 1. Startseite (Landing Page)

### Öffentliche Infos (vor Login)

```
┌─────────────────────────────────────────────┐
│  🌿 CSC Leipzig e.V.                        │
│  Cannabis Social Club                       │
├─────────────────────────────────────────────┤
│                                             │
│  Willkommen im CSC Leipzig!                │
│                                             │
│  📊 Club-Statistiken:                      │
│  • Gegründet: 15.03.2024                   │
│  • Mitglieder: 342/500                     │
│  • Aktive Sorten: 12                       │
│  • Geleistete Arbeitsstunden: 1.247h       │
│                                             │
│  [Mitglied werden] [Login]                 │
│                                             │
└─────────────────────────────────────────────┘
```

### Konfigurierbar durch Admin

```python
class ClubSettings(models.Model):
    """Einstellungen für öffentliche Startseite"""
    
    # Anzeige-Optionen
    show_founding_date = models.BooleanField(default=True)
    show_member_count = models.BooleanField(default=True)
    show_strain_count = models.BooleanField(default=True)
    show_work_hours = models.BooleanField(default=True)
    
    # Inhalt
    club_name = models.CharField(max_length=255)
    founding_date = models.DateField()
    welcome_text = models.TextField()
    
    # Statistiken (automatisch aktualisiert)
    member_count_public = models.IntegerField(default=0)
    strain_count_public = models.IntegerField(default=0)
    total_work_hours = models.IntegerField(default=0)
```

### Admin: Startseite konfigurieren

```
Startseite-Einstellungen

Anzeige-Optionen:
[✓] Gründungsdatum anzeigen
[✓] Mitgliederanzahl anzeigen
[✓] Sortenanzahl anzeigen
[✓] Arbeitsstunden anzeigen

Inhalt:
Club-Name: [CSC Leipzig e.V.___________]
Gründungsdatum: [15.03.2024____]

Willkommenstext:
[textarea]

[Aktualisieren]
```

---

## 2. Mitglieder-Shop (nach Login)

### Dashboard nach Login

```
Hallo Max! 👋

┌─────────────────────────────────────────────┐
│ Mein Guthaben: €47.50                      │
│ Mitgliedsnummer: #12345                    │
│ Letzte Bestellung: 25.02.2026              │
│ Verbrauch diesen Monat: 12g / 50g          │
└─────────────────────────────────────────────┘

Schnellzugriff:
[🛒 Jetzt bestellen]  [📦 Meine Bestellungen]
[💰 Guthaben aufladen] [📋 Meine Daten]
```

### Navigation

```
[Logo] CSC Leipzig                    [Guthaben: €47.50] [👤 Max] [🛒 2]

[Start] [Shop] [Meine Bestellungen] [Guthaben] [Profil] [Logout]
```

---

## 3. Shop-Oberfläche

### Kategorien (Dropdown/Filter)

```python
class ProductCategory(models.Model):
    """Produktkategorien"""
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Emoji oder Icon-Klasse
    
    # Kategorien:
    # - cannabis-sorten (Cannabis-Blüten)
    # - stecklinge (Stecklinge/Pflanzen)
    # - raucherzubehoer (Papers, Filter, etc.)
    # - cbd-produkte (CBD-Öl, etc.)
    # - merchandise (T-Shirts, etc.)
```

### Shop-Seite

```
🛒 CSC Shop

Filter: [Alle Kategorien ▼] [Alle Sorten ▼] [Preis: Low to High ▼]

Kategorien:
[🌿 Cannabis] [🌱 Stecklinge] [📦 Zubehör] [🛍️ Merchandise]

┌─────────────────────────────────────────────┐
│ 🌿 Orange Bud                              │
│ Cannabis-Sorte                             │
│ THC: 18% | CBD: 0.5%                      │
│ Aroma: Zitrus, Süß                         │
│                                            │
│ 💰 €10.00 / Gramm                         │
│                                            │
│ Menge: [3g ▼]                             │
│                                            │
│ Verfügbar: 2.847g                         │
│                                            │
│ [🛒 In den Warenkorb]                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 🌱 Northern Lights Stecklinge              │
│ Junge Pflanzen                             │
│                                            │
│ 💰 €15.00 / Stück                         │
│                                            │
│ Menge: [2 ▼] Stück                        │
│                                            │
│ Verfügbar: 23 Stück                        │
│                                            │
│ [🛒 In den Warenkorb]                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 📦 RAW Papers King Size                     │
│ Raucherzubehör                             │
│                                            │
│ 💰 €2.50 / Packung                        │
│                                            │
│ Menge: [5 ▼] Packungen                    │
│                                            │
│ Verfügbar: 150 Packungen                  │
│                                            │
│ [🛒 In den Warenkorb]                     │
└─────────────────────────────────────────────┘
```

### Mengenauswahl

| Produkttyp | Mengen-Optionen |
|------------|-----------------|
| Cannabis | 1g, 2g, 3g, 5g, 10g, 25g (max) |
| Stecklinge | 1, 2, 3, 5 Stück |
| Zubehör | 1-50 Stück (freie Eingabe) |

---

## 4. Warenkorb

```
🛒 Warenkorb

┌─────────────────────────────────────────────┐
│ Produkte:                                  │
├─────────────────────────────────────────────┤
│ 🌿 Orange Bud                              │
│ 3g × €10.00 = €30.00                      │
│ Charge: #240301-OB                         │
│ [🗑️ Entfernen]                            │
├─────────────────────────────────────────────┤
│ 🌱 Northern Lights Stecklinge              │
│ 2 Stück × €15.00 = €30.00                 │
│ [🗑️ Entfernen]                            │
├─────────────────────────────────────────────┤
│ 📦 RAW Papers                               │
│ 5 Packungen × €2.50 = €12.50              │
│ [🗑️ Entfernen]                            │
├─────────────────────────────────────────────┤
│ Gutscheincode: [________] [Anwenden]      │
│                                            │
│ Zwischensumme: €72.50                     │
│ Gutschein: -€5.00                         │
│ ─────────────────────────                  │
│ Gesamtsumme: €67.50                       │
│                                            │
│ Aktuelles Guthaben: €47.50                │
│ Restbetrag zu zahlen: €20.00              │
│                                            │
│ [💰 Mit Guthaben bezahlen]                │
│ [💳 Weiter zu Stripe →]                   │
└─────────────────────────────────────────────┘
```

### Gutscheincode

```python
class Voucher(models.Model):
    """Gutscheincodes"""
    
    code = models.CharField(max_length=20, unique=True)  # z.B. "WELCOME10"
    discount_amount = models.DecimalField(max_digits=6, decimal_places=2)  # €5.00
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True)  # 10%
    
    valid_from = models.DateField()
    valid_until = models.DateField()
    max_uses = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
```

---

## 5. Guthaben-System (Wallet)

### Konzept: Virtuelles Guthaben = Echtgeld
- • 1€ Guthaben = 1€ echtes Geld
- • Mitglied lädt Guthaben auf (Stripe)
- • Bestellungen werden mit Guthaben bezahlt
- • Keine "Credits" oder "Punkte" - echtes Geld

### Guthaben-Modell

```python
class Wallet(models.Model):
    """Virtuelles Guthaben eines Mitglieds"""
    
    member = models.OneToOneField(Member, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Limits
    max_balance = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    
    updated_at = models.DateTimeField(auto_now=True)

class WalletTransaction(models.Model):
    """Transaktionen (Aufladungen & Ausgaben)"""
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    
    TRANSACTION_TYPES = [
        ('topup', 'Aufladung'),
        ('purchase', 'Einkauf'),
        ('refund', 'Rückerstattung'),
    ]
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Positiv oder Negativ
    description = models.CharField(max_length=255)
    
    # Bei Aufladung: Stripe-Zahlung
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    
    # Bei Einkauf: Verknüpfung zu Bestellung
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

### Guthaben-Aufladung

```
💰 Guthaben aufladen

Aktuelles Guthaben: €47.50

Betrag auswählen:
[€10] [€25] [€50] [€100] [Eigenen Betrag]

[💳 Jetzt aufladen mit Stripe →]

Hinweis: Aufladungen sind keine Spenden und nicht steuerlich absetzbar.
```

### Stripe-Aufladung
```python
def topup_wallet(member, amount):
    """Guthaben via Stripe aufladen"""
    
    # Stripe Checkout Session erstellen
    session = stripe.checkout.Session.create(
        payment_method_types=['card', 'sepa_debit'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {
                    'name': f'Guthaben-Aufladung CSC {member.member_number}',
                },
                'unit_amount': int(amount * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f'{settings.SITE_URL}/wallet/success?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{settings.SITE_URL}/wallet/cancel',
        metadata={
            'member_id': member.id,
            'type': 'wallet_topup',
        }
    )
    
    return session.url
```

---

## 6. Limits-Prüfung (Hard Enforcement)

### Prüfung vor Bestellung

```python
def check_order_limits(member, cart_items):
    """
    Prüfe alle Limits vor Bestellabschluss.
    Wirft ValidationError wenn Limits überschritten.
    """
    
    # 1. Tageslimit (25g)
    today_consumption = get_today_consumption(member)
    today_new = sum(item['quantity'] for item in cart_items if item['category'] == 'cannabis')
    
    if today_consumption + today_new > 25:
        raise ValidationError(
            f"Tageslimit überschritten! "
            f"Heute bereits: {today_consumption}g, "
            f"Neu: {today_new}g, "
            f"Max: 25g"
        )
    
    # 2. Monatslimit (50g)
    month_consumption = get_month_consumption(member)
    month_new = today_new
    
    if month_consumption + month_new > 50:
        raise ValidationError(
            f"Monatslimit überschritten! "
            f"Diesen Monat bereits: {month_consumption}g, "
            f"Neu: {month_new}g, "
            f"Max: 50g"
        )
    
    # 3. THC-Limit (30g pro Monat) - optional
    month_thc = get_month_thc_consumption(member)
    new_thc = sum(
        item['quantity'] * (item['thc_content'] / 100)
        for item in cart_items if item['category'] == 'cannabis'
    )
    
    if month_thc + new_thc > 30:
        raise ValidationError(
            f"THC-Monatslimit überschritten! Max: 30g THC"
        )
    
    # 4. Alters-Check für <21
    if member.age < 21:
        for item in cart_items:
            if item['thc_content'] > 10:
                raise ValidationError(
                    f"Für Mitglieder unter 21 Jahren max 10% THC!"
                )
```

### Anzeige im Warenkorb

```
⚠️ Limit-Check

✅ Tageslimit: 12g / 25g (noch 13g möglich)
✅ Monatslimit: 35g / 50g (noch 15g möglich)
✅ THC-Gehalt: Für dein Alter erlaubt

[Bestellung abschließen]
```

---

## 7. SEPA-Lastschrift bei Registrierung

### Flow

```
1. Mitglied registriert sich
        ↓
2. Vorstand genehmigt
        ↓
3. Mitglied setzt Passwort
        ↓
4. SEPA-Mandat einrichten:
   - IBAN eingeben
   - Mandat bestätigen
   - 1 Cent-Test-Lastschrift
        ↓
5. Monatliche Abbuchung aktiviert
```

### SEPA-Mandat

```python
class SEPAMandate(models.Model):
    """SEPA-Lastschrift-Mandat"""
    
    member = models.OneToOneField(Member, on_delete=models.CASCADE)
    
    # Bankdaten
    iban = models.CharField(max_length=34)
    bic = models.CharField(max_length=11, blank=True)
    account_holder = models.CharField(max_length=255)
    
    # Mandat
    mandate_reference = models.CharField(max_length=35, unique=True)  # z.B. "CSC-12345-001"
    mandate_signed_at = models.DateTimeField()
    mandate_signature = models.TextField()  # Elektronische Unterschrift
    
    # Stripe
    stripe_payment_method_id = models.CharField(max_length=255)
    
    is_active = models.BooleanField(default=True)
```

### Mandat-Formular

```
📋 SEPA-Lastschrift-Mandat

Hiermit ermächtige ich den CSC Leipzig e.V.,
Zahlungen von meinem Konto mittels Lastschrift
einzuziehen.

Kontoinhaber: [Max Mustermann_________]
IBAN: [DE12 3456 7890 1234 5678 90___]
BIC: [______________________________]

Mandatsreferenz: CSC-12345-001

Zahlungsarten:
[✓] Mitgliedsbeitrag (monatlich €24)
[✓] Einkäufe im Shop

Ich kann innerhalb von 8 Wochen, beginnend mit dem
Belastungsdatum, die Erstattung des belasteten
Betrags verlangen.

[✓] Ich akzeptiere das Mandat

[Mandat erteilen]
```

---

## 8. "Meine Bestellungen"

```
📦 Meine Bestellungen

┌─────────────────────────────────────────────┐
│ Bestellung #12345                           │
│ Datum: 25.02.2026                          │
│ Status: ✅ Abgeschlossen                    │
│ Gesamt: €45.00                             │
│                                             │
│ Produkte:                                  │
│ • Orange Bud 3g (€30.00)                   │
│ • Stecklinge 1x (€15.00)                   │
│                                             │
│ [Details anzeigen]                         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Bestellung #12344                           │
│ Datum: 10.02.2026                          │
│ Status: 🚚 Bereit zur Abholung              │
│ Gesamt: €25.00                             │
│                                             │
│ [Details anzeigen]                         │
└─────────────────────────────────────────────┘
```

### Bestellstatus
- • 🛒 **Warenkorb** - Noch nicht bestellt
- • ⏳ **Zahlung ausstehend** - Warte auf Zahlung
- • ✅ **Bezahlt** - Zahlung eingegangen
- • 🚚 **Bereit zur Abholung** - Paket zusammengestellt
- • 📦 **Abgeholt** - Vom Mitglied abgeholt
- • ❌ **Storniert** - Bestellung storniert

---

## Nächste Schritte

1. [ ] Shop-Models erstellen (Product, Category, Order)
2. [ ] Warenkorb-System implementieren
3. [ ] Guthaben-System (Wallet)
4. [ ] Stripe-Integration für Guthaben
5. [ ] Limits-Prüfung (Middleware)
6. [ ] SEPA-Mandat-Formular
7. [ ] Bestell-Historie

---

**Verwandte Dokumente:**
- [18-zahlungs-system.md](./18-zahlungs-system.md) - Stripe Checkout
- [22-arbeitsstunden-zahlungen.md](./22-arbeitsstunden-zahlungen.md) - Mitgliedsbeitrag