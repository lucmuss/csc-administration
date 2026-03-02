# GUI-Design - ASCII Mockups

> Textuelle Layouts für Hauptscreens
> Stand: 2. März 2026

---

## 📱 Mobile App - Mitgliederbereich

### Screen 1: Login
```
┌─────────────────────────┐
│                         │
│    🌿 CSC Leipzig       │
│       Süd e.V.          │
│                         │
│  ┌─────────────────┐    │
│  │ E-Mail          │    │
│  └─────────────────┘    │
│                         │
│  ┌─────────────────┐    │
│  │ Passwort        │    │
│  └─────────────────┘    │
│                         │
│  ┌─────────────────┐    │
│  │     LOGIN       │    │
│  └─────────────────┘    │
│                         │
│  Passwort vergessen?    │
│                         │
└─────────────────────────┘
```

### Screen 2: Dashboard (Mitglied)
```
┌─────────────────────────┐
│ ≡  CSC Leipzig Süd   🔔 │  ← Menu + Notifications
├─────────────────────────┤
│                         │
│  Hallo Max! 👋          │
│                         │
│  ┌─────────────────┐    │
│  │ GUTHABEN        │    │
│  │    € 42,50      │    │
│  │ [Aufladen]      │    │
│  └─────────────────┘    │
│                         │
│  DEINE LIMITS:          │
│  ┌─────────┬────────┐   │
│  │ Monat   │ Tag    │   │
│  │ 12g/50g │ 0g/25g│   │
│  └─────────┴────────┘   │
│                         │
│  ┌─────────────────┐    │
│  │  🛒 BESTELLEN   │    │
│  └─────────────────┘    │
│                         │
│  Letzte Bestellung:     │
│  📦 5g Blue Dream       │
│     (12.03. - Abgeholt) │
│                         │
├─────────────────────────┤
│ 🏠  🛒  📋  💬  👤    │  ← Navigation
└─────────────────────────┘
```

### Screen 3: Sorten-Übersicht
```
┌─────────────────────────┐
│ ←  VERFÜGBARE SORTEN  🔍│
├─────────────────────────┤
│ [Alle] [Blüten] [Steck] │  ← Filter
├─────────────────────────┤
│                         │
│ ┌─────────────────────┐ │
│ │ 🌿 Blue Dream       │ │
│ │ Indica | 8% THC     │ │
│ │ € 8,50/g | A+ Quali │ │
│ │ [+ In den Warenkorb]│ │
│ └─────────────────────┘ │
│                         │
│ ┌─────────────────────┐ │
│ │ 🌿 Orange Bud       │ │
│ │ Sativa | 12% THC    │ │
│ │ € 9,00/g | A Quali  │ │
│ │ ⚠️ Nur noch 5g      │ │
│ │ [+ In den Warenkorb]│ │
│ └─────────────────────┘ │
│                         │
│ ┌─────────────────────┐ │
│ │ 🌱 Stecklinge       │ │
│ │ Orange Sherbert     │ │
│ │ € 5,00/Stück        │ │
│ │ [+ In den Warenkorb]│ │
│ └─────────────────────┘ │
│                         │
├─────────────────────────┤
│ 🛒 Warenkorb: 2 Artikel │
│     € 42,50  [Bestellen]│
└─────────────────────────┘
```

### Screen 4: Warenkorb & Bestellung
```
┌─────────────────────────┐
│ ←  WARENKORB            │
├─────────────────────────┤
│                         │
│ ┌─────────────────────┐ │
│ │ 🌿 Blue Dream    🗑️ │ │
│ │ 3g × € 8,50 = €25,50│ │
│ │ [ - ]  3g  [ + ]    │ │
│ └─────────────────────┘ │
│                         │
│ ┌─────────────────────┐ │
│ │ 🌿 Orange Bud    🗑️ │ │
│ │ 2g × € 9,00 = €18,00│ │
│ │ [ - ]  2g  [ + ]    │ │
│ └─────────────────────┘ │
│                         │
├─────────────────────────┤
│  Zwischensumme: €43,50  │
│  Verfügbares Guthaben:  │
│  € 42,50                │
│                         │
│  ⚠️ Guthaben reicht     │
│     nicht aus!          │
│                         │
│  [+ Guthaben aufladen]  │
│                         │
│  ┌─────────────────┐    │
│  │   BESTELLEN     │    │  ← Disabled
│  └─────────────────┘    │
│                         │
└─────────────────────────┘
```

---

## 💻 Desktop - Admin Dashboard

### Screen 5: Admin Dashboard
```
┌────────────────────────────────────────────────────────────────┐
│  🌿 CSC Admin           Dashboard    Mitglieder    Finanzen  ⚙️ │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  GUTEN MORGEN, LUCAS!                    ┌──────────────┐     │
│                                          │ Schnell-Links│     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  ├──────────────┤     │
│  │ NEUE     │ │ AUSGABEN │ │ OFFENE   │  │ + Neues      │     │
│  │ MITGLIED │ │ HEUTE    │ │ POSTEN   │  │   Mitglied   │     │
│  │    3     │ │ € 1.250  │ │   12     │  │ + Ausgabe    │     │
│  │ ↑ +2     │ │ ↑ +15%   │ │ ↓ -3     │  │   buchen     │     │
│  └──────────┘ └──────────┘ └──────────┘  │ + Charge     │     │
│                                          │   anlegen    │     │
│  ⚠️ WARNUNGEN:                           └──────────────┘     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 🔴 Niedriger Bestand: Orange Bud (nur noch 50g)       │   │
│  │ 🟡 Offene Zahlungen: 3 Mitglieder > 14 Tage           │   │
│  │ 🟡 Unvollständige Verifizierungen: 5 Mitglieder       │   │
│  │ 🔵 Mitgliederversammlung: Einladung in 2 Tagen        │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  AKTIVITÄTEN (Letzte 24h):                                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 09:30  Max M.        │ Registrierung abgeschlossen      │   │
│  │ 09:15  Anna K.       │ Ausgabe: 5g Blue Dream           │   │
│  │ 08:45  System        │ Tägliches Backup erstellt        │   │
│  │ 08:30  Tom S.        │ Zahlung eingegangen: € 50        │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Screen 6: Mitglieder-Liste
```
┌────────────────────────────────────────────────────────────────┐
│  🌿 CSC Admin    ← Dashboard    [Mitglieder]    Finanzen  ⚙️  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  MITGLIEDER (487 gesamt)                           [+ Neu]     │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔍 Suchen...    [Status ▼]  [PLZ ▼]    [Filter] [⚙️]   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────┬──────────────┬────────┬──────────┬────────┐  │
│  │ [ ] Name    │ E-Mail       │ Status │ Guthaben │ Aktion │  │
│  ├─────────────┼──────────────┼────────┼──────────┼────────┤  │
│  │ [ ] ████    │ m@mail.com   │ ✅ Akt │ € 42,50  │ 👁 ✏️ 🗑│  │
│  │ [ ] ████    │ a@mail.com   │ ⏳ Aus │ € 0,00   │ 👁 ✏️ 🗑│  │
│  │ [ ] ████    │ t@mail.com   │ 🔴 Ges │ -€ 25,00 │ 👁 ✏️ 🗑│  │
│  │ [ ] ████    │ s@mail.com   │ 🆕 Neu │ € 0,00   │ 👁 ✏️ 🗑│  │
│  │ [ ] ████    │ l@mail.com   │ ✅ Akt │ € 150,00 │ 👁 ✏️ 🗑│  │
│  └─────────────┴──────────────┴────────┴──────────┴────────┘  │
│                                                                │
│  [ ] Alle auswählen    [Massenaktion ▼]          ← 1 2 3 … 49 →│
│                                                                │
│  Zeige 1-20 von 487                                            │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Screen 7: Mitglied-Detail
```
┌────────────────────────────────────────────────────────────────┐
│  🌿 CSC Admin    ← Mitglieder    Max Mustermann (100086)    ✕ │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────┐                                                  │
│  │    👤    │  Max Mustermann                    [✏️ Bearb.]  │
│  │          │  Mitgliedsnummer: 100086           [🗑 Lösch.]  │
│  │          │  Status: ✅ Aktiv seit 01.01.2025               │
│  └──────────┘                                                  │
│                                                                │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐        │
│  │ 📋 PERSÖNLICH │ │ 💰 FINANZEN   │ │ 📦 BESTELLUN  │        │
│  └───────────────┘ └───────────────┘ └───────────────┘        │
│                                                                │
│  KONTAKT:                              LIMITS:                 │
│  ─────────────────────────────────    ─────────────────        │
│  Max Mustermann                        Monat: 12g / 50g        │
│  Musterstraße 123                      Tag:   0g  / 25g        │
│  04123 Leipzig                                                 │
│  📧 max@mail.com                                               │
│  📱 0049151123456789                                           │
│                                                                │
│  BANKDATEN:                            GUTHABEN:               │
│  ─────────────────────────────────    ─────────────────        │
│  IBAN: DE12 3456 7890 1234 5678 90     € 42,50                 │
│  BIC:  BELADEBEXXX                     [+ Aufladen]            │
│  Mandat: CSC-100086-2025 (✅ Aktiv)                           │
│                                                                │
│  VERIFIZIERUNG:                                                │
│  ─────────────────────────────────                             │
│  Status: ✅ Verifiziert (12.01.2025)                          │
│  Dokumente: Ausweis ✅, Wohnsitz ✅                           │
│                                                                │
│  LETZTE AKTIVITÄTEN:                                           │
│  ─────────────────────────────────                             │
│  12.03.  Ausgabe: 5g Blue Dream                   € 42,50      │
│  01.03.  Zahlung eingegangen                      € 50,00      │
│  28.02.  Bestellung #1234 aufgegeben              € 42,50      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 📟 Kiosk/Tablet - Ausgabestation

### Screen 8: Ausgabe-Station
```
┌────────────────────────────────────────────────────────────────┐
│                     🌿 CSC LEIPZIG SÜD                         │
│                       AUSGABESTATION                           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│                    ┌──────────────┐                            │
│                    │              │                            │
│                    │   📷📷📷     │                            │
│                    │   QR-CODE    │                            │
│                    │   SCANNEN    │                            │
│                    │              │                            │
│                    └──────────────┘                            │
│                                                                │
│            --- ODER ---                                        │
│                                                                │
│            ┌────────────────────┐                              │
│            │ MITGLIEDSNUMMER    │                              │
│            └────────────────────┘                              │
│                                                                │
│            ┌────────────────────┐                              │
│            │     BESTÄTIGEN     │                              │
│            └────────────────────┘                              │
│                                                                │
│  ───────────────────────────────────────────────────────────  │
│  Status: Bereit                                               │
│  Angemeldet: Mitarbeiter Luca (ID: 1001)                     │
└────────────────────────────────────────────────────────────────┘
```

### Screen 9: Ausgabe-Bestätigung
```
┌────────────────────────────────────────────────────────────────┐
│                     🌿 CSC LEIPZIG SÜD                         │
│                       AUSGABESTATION                           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ✅ MITGLIED ERKANNT                                           │
│                                                                │
│  ┌────────────────────────────────────┐                        │
│  │                                    │                        │
│  │  👤 Max Mustermann                 │                        │
│  │     #100086                        │                        │
│  │                                    │                        │
│  │  STATUS: ✅ Aktiv                  │                        │
│  │                                    │                        │
│  │  VERFÜGBARE LIMITS:                │                        │
│  │  Monat: 12g / 50g                  │                        │
│  │  Tag:    0g / 25g  ✅              │                        │
│  │                                    │                        │
│  └────────────────────────────────────┘                        │
│                                                                │
│  AUSGABE BUCHEN:                                               │
│  ┌────────────────────────────────────┐                        │
│  │ Sorte: [Blue Dream         ▼]     │                        │
│  │ Charge: [A+ 03/2025        ▼]     │                        │
│  │ Menge:  [5                ] g      │                        │
│  └────────────────────────────────────┘                        │
│                                                                │
│  ┌────────────────────────────────────┐                        │
│  │     ✅ AUSGABE BESTÄTIGEN          │                        │
│  └────────────────────────────────────┘                        │
│                                                                │
│  [❌ Abbrechen]                                                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Design-Prinzipien

1. **Mobile First**: Alle Screens funktionieren auf 375px Breite
2. **Klare Hierarchie**: Wichtige Aktionen prominent (große Buttons)
3. **Status-Farben**:
   - ✅ Grün = OK
   - 🟡 Gelb = Warnung/Achtung
   - 🔴 Rot = Fehler/Kritisch
   - 🔵 Blau = Info/Neutral
   - 🆕 Blau = Neu

4. **Konsistente Navigation**:
   - Mobile: Bottom-Navigation (5 Icons)
   - Desktop: Top-Navigation (Text + Icons)

5. **Touch-Optimierung**:
   - Buttons min. 44px Höhe
   - Abstände min. 8px
   - Klare Touch-Targets

---

**Nächste Schritte:**
- [ ] Wireframes mit Figma erstellen
- [ ] Farbschema definieren (Primary/Secondary)
- [ ] Typografie festlegen
- [ ] Icon-Set auswählen
