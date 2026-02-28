# Sorten-Datenbank & Warenwirtschaft

**Dokumentation:** Strains, Inventory Management, einfaches UI

---

## Grundprinzip: Funktionalität > Design

**Wichtig:**
- • Erst ALLE Features implementieren
- • Dann Styling/Optik
- • Tailwind CSS Standard (kein Custom-Design jetzt)
- • Einfache, übersichtliche Tabellen
- • Keine Animationen, keine Effekte
- • Mobile-responsive (später optimieren)

---

## Datenbank-Modell: Sorten (Strains)

### Strain (Sorte)
```python
class Strain(models.Model):
    """Cannabis Sorte (unabhängig von Charge)"""
    
    # Basis-Info
    name = models.CharField(max_length=255)  # "Orange Bud"
    slug = models.SlugField(unique=True)  # "orange-bud"
    
    # Genetik
    GENETIK_CHOICES = [
        ('indica', 'Indica'),
        ('sativa', 'Sativa'),
        ('hybrid', 'Hybrid'),
        ('ruderalis', 'Ruderalis'),
    ]
    genetik = models.CharField(max_length=20, choices=GENETIK_CHOICES)
    
    # Beschreibung
    description = models.TextField(blank=True)
    aroma = models.CharField(max_length=255, blank=True)  # "Zitrus, Erdig"
    effects = models.TextField(blank=True)  # "Entspannend, Euphorisierend"
    
    # THC/CBD Durchschnittswerte (Referenz)
    thc_content_avg = models.DecimalField(max_digits=4, decimal_places=2)
    cbd_content_avg = models.DecimalField(max_digits=4, decimal_places=2)
    
    # Anbau-Info
    flowering_time_days = models.IntegerField(null=True, blank=True)  # Blütezeit
    yield_indoor_g_per_plant = models.IntegerField(null=True, blank=True)
    difficulty = models.CharField(max_length=20, choices=[
        ('easy', 'Anfänger'),
        ('medium', 'Fortgeschritten'),
        ('hard', 'Experte'),
    ], blank=True)
    
    # Medizinisch
    medical_use = models.TextField(blank=True)  # "Schmerzen, Schlafstörungen"
    
    # Verwaltung
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
```

### Charge (Batch) - konkreter Anbau
```python
class Batch(models.Model):
    """Konkrete Charge eines Anbaus"""
    
    # Verknüpfung
    strain = models.ForeignKey(Strain, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=50, unique=True)  # "240301-OB"
    
    # Chargen-Info
    harvest_date = models.DateField()
    total_harvested_grams = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Aktueller Bestand
    available_grams = models.DecimalField(max_digits=10, decimal_places=2)
    reserved_grams = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Labordaten (optional)
    lab_tested = models.BooleanField(default=False)
    thc_content_actual = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cbd_content_actual = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    lab_report_file = models.FileField(upload_to='lab_reports/', null=True, blank=True)
    
    # Preis
    price_per_gram = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Status
    STATUS_CHOICES = [
        ('growing', 'Im Anbau'),
        ('curing', 'Curing/Trocknung'),
        ('available', 'Verfügbar'),
        ('low_stock', 'Fast ausverkauft'),
        ('sold_out', 'Ausverkauft'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='growing')
    
    # Stripe (für Zahlungen)
    stripe_product_id = models.CharField(max_length=255, blank=True)
    stripe_price_id = models.CharField(max_length=255, blank=True)
    
    # Dokumentation
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-harvest_date']
    
    def __str__(self):
        return f"{self.strain.name} - {self.batch_number}"
    
    @property
    def sold_grams(self):
        return self.total_harvested_grams - self.available_grams
    
    @property
    def sold_percentage(self):
        if self.total_harvested_grams == 0:
            return 0
        return (self.sold_grams / self.total_harvested_grams) * 100
```

### Inventory Transaction (Bestandsbewegung)
```python
class InventoryTransaction(models.Model):
    """Jede Bewegung im Bestand"""
    
    TRANSACTION_TYPES = [
        ('initial', 'Erstbuchung (Ernte)'),
        ('sale', 'Verkauf/Ausschank'),
        ('adjustment', 'Korrektur'),
        ('loss', 'Verlust/Schwund'),
    ]
    
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    
    # Menge
    amount_grams = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Referenz (wenn Verkauf)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Wer hat es gebucht?
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Grund (bei Korrektur/Verlust)
    reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
```

---

## Warenwirtschaft - Features

### 1. Bestandsübersicht (Dashboard)

**Einfache Tabelle:**
```
┌──────────────┬─────────────┬────────────┬───────────┬─────────┬──────────┐
│ Sorte        │ Charge      │ THC        │ Verfügbar │ Status  │ Aktionen │
├──────────────┼─────────────┼────────────┼───────────┼─────────┼──────────┤
│ Orange Bud   │ 240301-OB   │ 18%        │ 2.847g    │ ✅ OK   │ [Details]│
│ Blue Dream   │ 240228-BD   │ 20%        │ 1.523g    │ ⚠️ Low  │ [Details]│
│ Northern L.  │ 240215-NL   │ 22%        │ 0g        │ ❌ Sold │ [Details]│
└──────────────┴─────────────┴────────────┴───────────┴─────────┴──────────┘
```

**Filter:**
- • Nach Status (alle, verfügbar, low stock, ausverkauft)
- • Nach THC-Gehalt (<10%, 10-15%, 15-20%, >20%)
- • Nach Sorte
- • Nach Datum

### 2. Chargen-Details

**Detail-Ansicht:**
```
Orange Bud - Charge #240301-OB

┌────────────────────────────────────────┐
│ Basis-Info                             │
│ Genetik: Hybrid (60% Indica)          │
│ THC: 18% | CBD: 0.5%                  │
│ Aroma: Zitrus, Erdig                   │
│                                        │
│ Diese Charge:                          │
│ Anbau-Datum: 01.03.2024               │
│ Ernte-Datum: 15.04.2024               │
│ Gesamtertrag: 3.000g                  │
│ Verfügbar: 2.847g (95%)               │
│ Verkauft: 153g (5%)                   │
│                                        │
│ Preis: €10.00 / Gramm                 │
│ Status: ✅ Verfügbar                   │
│                                        │
│ [Bestand anpassen] [Deaktivieren]     │
└────────────────────────────────────────┘
```

### 3. Neue Charge einbuchen

**Formular:**
```
Neue Charge einbuchen

Sorte: [Orange Bud ▼] oder [+ Neue Sorte anlegen]

Charge-Nummer: [240301-OB_________] (Auto-generieren?)

Ernte-Datum: [__/__/____]

Gesamtmenge (g): [3000______]

THC-Gehalt (%): [18____]

CBD-Gehalt (%): [0.5___]

Preis pro Gramm (€): [10.00___]

Labortest vorhanden? [ ] Ja
[Datei hochladen]

Notizen:
[Textarea]

[Charge einbuchen]
```

**Nach Einbuchung:**
- • Automatisch Stripe-Produkt anlegen
- • Im Shop verfügbar machen
- • Bestand = Gesamtmenge

### 4. Bestandswarnungen

**Automatische Alerts:**
```python
# Wenn Bestand unter Schwellenwert
if batch.available_grams < 100:
    batch.status = 'low_stock'
    send_alert_to_staff(f"{batch.strain.name} fast ausverkauft!")

# Wenn ausverkauft
if batch.available_grams <= 0:
    batch.status = 'sold_out'
    batch.is_active = False
    send_alert_to_staff(f"{batch.strain.name} ausverkauft!")
```

**Dashboard-Widget:**
```
⚠️ Bestandswarnungen

• Orange Bud - Charge 240301-OB: Noch 2.847g (OK)
• Blue Dream - Charge 240228-BD: Noch 123g (LOW!)
• Northern Lights - Charge 240215-NL: AUSVERKAUFT
```

### 5. Inventur

**Inventur-Modus:**
```
Inventur durchführen

Orange Bud - Charge 240301-OB
System-Bestand: 2.847g
Tatsächlicher Bestand: [_______] g

Differenz: [Auto-berechnet]

Grund für Differenz:
[ ] Schwund (Trocknung)
[ ] Fehlbuchung
[ ] Verlust
[ ] Sonstiges

[Bestand korrigieren]
```

**Inventur-Report:**
- • Datum
- • Wer hat Inventur gemacht
- • Alle Chargen
- • Differenzen
- • Gesamtwert

---

## UI/UX - Einfach gehalten

### Design-Prinzipien
1. **Klare Hierarchie** - Wichtiges zuerst
2. **Tabellen statt Kacheln** (einfacher)
3. **Formulare übersichtlich**
4. **Farben nur für Status** (grün/gelb/rot)
5. **Keine Animationen**
6. **Mobile: funktioniert, aber nicht optimiert**

### Tailwind CSS Standard
```html
<!-- Einfache Tabelle -->
<table class="w-full border-collapse">
  <thead>
    <tr class="bg-gray-100">
      <th class="p-2 text-left">Sorte</th>
      <th class="p-2 text-left">Charge</th>
      <th class="p-2 text-right">Verfügbar</th>
    </tr>
  </thead>
  <tbody>
    <tr class="border-b">
      <td class="p-2">Orange Bud</td>
      <td class="p-2">240301-OB</td>
      <td class="p-2 text-right">2.847g</td>
    </tr>
  </tbody>
</table>

<!-- Einfacher Button -->
<button class="bg-blue-500 text-white px-4 py-2 rounded">
  Charge einbuchen
</button>

<!-- Status-Badge -->
<span class="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
  Verfügbar
</span>
```

---

## Integration mit Bestellsystem

### Wenn Bestellung reinkommt:
```python
def process_order(order):
    for item in order.items:
        batch = item.batch
        
        # Bestand reduzieren
        batch.available_grams -= item.quantity_grams
        batch.reserved_grams += item.quantity_grams
        
        # Transaktion buchen
        InventoryTransaction.objects.create(
            batch=batch,
            transaction_type='sale',
            amount_grams=-item.quantity_grams,
            order=order,
            created_by=system_user
        )
        
        # Status aktualisieren
        batch.update_status()
        batch.save()
```

---

## Reports & Export

### Bestands-Report
- • Aktueller Bestand pro Charge
- • Gesamtwert (Bestand × Preis)
- • Umsatz pro Charge
- • Rotation (wie schnell verkauft?)

### Excel-Export
```
Sorte | Charge | Ernte | THC | CBD | Gesamt | Verfügbar | Preis | Status
```

---

## Nächste Schritte (Priorität)

1. [ ] Modelle erstellen (Strain, Batch, InventoryTransaction)
2. [ ] Admin-Interface für Chargen
3. [ ] Bestandsübersicht Dashboard
4. [ ] Automatische Stripe-Produkt-Anlage
5. [ ] Inventur-Funktion
6. [ ] Reports

---

**Verwandte Dokumente:**
- [18-zahlungs-system.md](./18-zahlungs-system.md) - Stripe-Integration, Preise
- [96-gesetzliche-pflicht-features.md](./96-gesetzliche-pflicht-features.md) - Chargen-Rückverfolgung
- [11-tech-stack.md](./11-tech-stack.md) - Tailwind CSS