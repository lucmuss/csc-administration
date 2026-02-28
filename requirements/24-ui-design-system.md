# UI/UX Design - RedFlag Analyzer Style

**Dokumentation:** Layout, Navigation, Icons, Mobile-First

---

## Design-Prinzip: RedFlag Analyzer Style

**Wichtig:**
- • **Kein eigenes Design erfinden!**
- • RedFlag Analyzer Layout als Vorlage verwenden
- • Identische Struktur und Komponenten
- • Farben anpassen (grün statt rot für CSC)
- • Eigene Icons (Cannabis-Theme)

---

## Layout-Struktur

### 1. Base Template (wie RedFlag)

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CSC Admin{% endblock %}</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'csc-green': '#2D5A27',  // Hauptfarbe (dunkelgrün)
                        'csc-light': '#4A7C42',  // Hellgrün
                        'csc-accent': '#7CB342', // Akzent
                    }
                }
            }
        }
    </script>
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    
    <!-- Alpine.js (für Mobile Menu) -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    
    {% block extra_head %}{% endblock %}
</head>
<body class="bg-gray-50 min-h-screen flex flex-col">
    
    <!-- Navigation -->
    {% include 'includes/navigation.html' %}
    
    <!-- Main Content -->
    <main class="flex-grow pt-16">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    {% include 'includes/footer.html' %}
    
</body>
</html>
```

---

## 2. Navigation (wie RedFlag)

### Desktop Navigation

```html
<nav class="bg-white shadow-sm border-b border-gray-200 fixed top-0 left-0 right-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
            
            <!-- Logo -->
            <div class="flex items-center">
                <a href="{% url 'home' %}" class="text-xl font-bold text-csc-green flex items-center gap-2">
                    <span>🌿</span>
                    <span>CSC Admin</span>
                </a>
            </div>
            
            <!-- Desktop Menu (center/right) -->
            <div class="hidden md:flex items-center space-x-4">
                {% if user.is_authenticated %}
                    <!-- Guthaben-Anzeige -->
                    <a href="{% url 'wallet:detail' %}" 
                       class="flex items-center bg-green-50 text-csc-green px-3 py-1 rounded-full text-sm font-medium">
                        <span class="mr-1">💰</span>
                        <span>€{{ user.member.wallet.balance }}</span>
                    </a>
                    
                    <!-- Shop -->
                    <a href="{% url 'shop:index' %}" 
                       class="text-gray-700 hover:text-csc-green px-3 py-2 text-sm font-medium">
                        🛒 Shop
                    </a>
                    
                    <!-- Meine Bestellungen -->
                    <a href="{% url 'orders:list' %}" 
                       class="text-gray-700 hover:text-csc-green px-3 py-2 text-sm font-medium">
                        📦 Bestellungen
                    </a>
                    
                    <!-- Profil Dropdown -->
                    <div class="relative" x-data="{ open: false }">
                        <button @click="open = !open" 
                                class="flex items-center text-gray-700 hover:text-csc-green px-3 py-2">
                            <span class="mr-2">👤</span>
                            <span>{{ user.first_name }}</span>
                            <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                            </svg>
                        </button>
                        
                        <!-- Dropdown Menu -->
                        <div x-show="open" 
                             @click.away="open = false"
                             class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                            <a href="{% url 'profile' %}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                Mein Profil
                            </a>
                            <a href="{% url 'wallet:detail' %}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                💰 Guthaben
                            </a>
                            <hr class="my-1">
                            <a href="{% url 'account_logout' %}" class="block px-4 py-2 text-sm text-red-600 hover:bg-gray-100">
                                Abmelden
                            </a>
                        </div>
                    </div>
                {% else %}
                    <a href="{% url 'account_login' %}" class="text-gray-700 hover:text-csc-green px-3 py-2 text-sm font-medium">
                        Login
                    </a>
                    <a href="{% url 'membership:apply' %}" 
                       class="bg-csc-green hover:bg-csc-light text-white px-4 py-2 rounded-md text-sm font-medium">
                        Mitglied werden
                    </a>
                {% endif %}
            </div>
            
            <!-- Mobile: Guthaben + Hamburger -->
            <div class="md:hidden flex items-center space-x-2">
                {% if user.is_authenticated %}
                    <a href="{% url 'wallet:detail' %}" 
                       class="flex items-center bg-green-50 text-csc-green px-3 py-1 rounded-full text-sm">
                        <span class="mr-1">💰</span>
                        <span>€{{ user.member.wallet.balance }}</span>
                    </a>
                    
                    <!-- Hamburger Button -->
                    <button @click="mobileMenuOpen = !mobileMenuOpen" 
                            class="text-gray-700 hover:text-csc-green p-2">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M4 6h16M4 12h16M4 18h16"/>
                        </svg>
                    </button>
                {% else %}
                    <a href="{% url 'account_login' %}" class="text-gray-700 text-sm">Login</a>
                    <a href="{% url 'membership:apply' %}" 
                       class="bg-csc-green text-white px-3 py-2 rounded-md text-xs">
                        Registrieren
                    </a>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- Mobile Menu (Slide-down) -->
    <div x-show="mobileMenuOpen" 
         @click.away="mobileMenuOpen = false"
         class="md:hidden bg-white border-t border-gray-200"
         x-data="{ mobileMenuOpen: false }">
        <div class="px-2 pt-2 pb-3 space-y-1">
            {% if user.is_authenticated %}
                <a href="{% url 'shop:index' %}" 
                   class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-csc-green hover:bg-gray-50">
                    🛒 Shop
                </a>
                <a href="{% url 'orders:list' %}" 
                   class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-csc-green hover:bg-gray-50">
                    📦 Meine Bestellungen
                </a>
                <a href="{% url 'wallet:detail' %}" 
                   class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-csc-green hover:bg-gray-50">
                    💰 Guthaben
                </a>
                <a href="{% url 'profile' %}" 
                   class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-csc-green hover:bg-gray-50">
                    👤 Mein Profil
                </a>
                <hr class="my-2">
                <a href="{% url 'account_logout' %}" 
                   class="block px-3 py-2 rounded-md text-base font-medium text-red-600 hover:bg-gray-50">
                    Abmelden
                </a>
            {% else %}
                <a href="{% url 'account_login' %}" 
                   class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-csc-green hover:bg-gray-50">
                    Login
                </a>
                <a href="{% url 'membership:apply' %}" 
                   class="block px-3 py-2 rounded-md text-base font-medium text-csc-green hover:bg-gray-50">
                    Mitglied werden
                </a>
            {% endif %}
        </div>
    </div>
</nav>
```

---

## 3. Icons (Emoji-Set)

| Funktion | Icon | Beschreibung |
|----------|------|--------------|
| Logo | 🌿 | Cannabis-Blatt |
| Shop | 🛒 | Einkaufswagen |
| Guthaben | 💰 | Geldbeutel |
| Bestellungen | 📦 | Paket |
| Profil | 👤 | Person |
| Admin | ⚙️ | Zahnrad |
| Logout | 🚪 | Tür |
| Cannabis | 🌿 | Blatt |
| Stecklinge | 🌱 | Spross |
| Zubehör | 📦 | Box |
| Warnung | ⚠️ | Ausrufezeichen |
| Erfolg | ✅ | Häkchen |
| Fehler | ❌ | Kreuz |
| Info | ℹ️ | Info |
| E-Mail | ✉️ | Umschlag |
| Telefon | 📞 | Telefon |
| Kalender | 📅 | Kalender |
| Uhr | 🕐 | Uhr |
| Dokument | 📄 | Seite |
| Download | ⬇️ | Pfeil runter |
| Upload | ⬆️ | Pfeil hoch |
| Suchen | 🔍 | Lupe |
| Bearbeiten | ✏️ | Stift |
| Löschen | 🗑️ | Mülleimer |
| Speichern | 💾 | Diskette |
| Zurück | ← | Pfeil links |
| Weiter | → | Pfeil rechts |

---

## 4. Komponenten (wie RedFlag)

### Buttons

```html
<!-- Primary Button (grün) -->
<button class="bg-csc-green hover:bg-csc-light text-white px-4 py-2 rounded-md font-medium">
    Bestellen
</button>

<!-- Secondary Button (grau) -->
<button class="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-md font-medium">
    Abbrechen
</button>

<!-- Danger Button (rot) -->
<button class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md font-medium">
    Löschen
</button>

<!-- Outline Button -->
<button class="border border-csc-green text-csc-green hover:bg-csc-green hover:text-white px-4 py-2 rounded-md font-medium">
    Details
</button>
```

### Cards

```html
<!-- Produkt-Karte (wie RedFlag) -->
<div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
    <div class="p-4">
        <h3 class="text-lg font-semibold text-gray-900">Orange Bud</h3>
        <p class="text-sm text-gray-600 mt-1">THC: 18% | CBD: 0.5%</p>
        <div class="mt-4 flex justify-between items-center">
            <span class="text-xl font-bold text-csc-green">€10.00/g</span>
            <button class="bg-csc-green text-white px-4 py-2 rounded-md text-sm">
                In den Warenkorb
            </button>
        </div>
    </div>
</div>
```

### Formulare

```html
<!-- Input Field -->
<div class="space-y-2">
    <label class="block text-sm font-medium text-gray-700">
        E-Mail
    </label>
    <input type="email" 
           class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-csc-green focus:border-transparent"
           placeholder="max@example.com">
</div>

<!-- Select -->
<div class="space-y-2">
    <label class="block text-sm font-medium text-gray-700">
        Menge
    </label>
    <select class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-csc-green">
        <option>1g</option>
        <option>3g</option>
        <option>5g</option>
    </select>
</div>
```

### Alerts

```html
<!-- Success -->
<div class="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-md">
    ✅ Bestellung erfolgreich!
</div>

<!-- Error -->
<div class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md">
    ❌ Ein Fehler ist aufgetreten.
</div>

<!-- Warning -->
<div class="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-md">
    ⚠️ Limit fast erreicht!
</div>

<!-- Info -->
<div class="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-md">
    ℹ️ Neue Sorten verfügbar.
</div>
```

---

## 5. Seitenstruktur

### Landing Page (öffentlich)
```
┌─────────────────────────────────────────┐
│  🌿 CSC Admin                    [Login]│
├─────────────────────────────────────────┤
│                                         │
│  Willkommen beim CSC Leipzig!          │
│                                         │
│  📊 Statistiken:                       │
│  • 342 Mitglieder                      │
│  • 12 Sorten verfügbar                 │
│  • 1.247h geleistet                    │
│                                         │
│  [Mitglied werden]                      │
│                                         │
├─────────────────────────────────────────┤
│  Footer                                 │
└─────────────────────────────────────────┘
```

### Mitglieder-Dashboard (nach Login)
```
┌─────────────────────────────────────────┐
│  🌿 CSC Admin    💰 €47.50  👤 Max [▼] │
├─────────────────────────────────────────┤
│                                         │
│  Hallo Max! 👋                          │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Guthaben: €47.50               │   │
│  │ Monatsverbrauch: 12g / 50g     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [🛒 Jetzt bestellen]                   │
│                                         │
│  Aktuelle Sorten:                       │
│  [Orange Bud] [Blue Dream] [...]       │
│                                         │
└─────────────────────────────────────────┘
```

---

## 6. Responsive Breakpoints

Wie RedFlag:
- • **Mobile:** < 768px (Hamburger-Menü)
- • **Tablet:** 768px - 1024px
- • **Desktop:** > 1024px (volles Menü)

---

## 7. CSS-Klassen (Tailwind)

### Häufig verwendete Klassen
```css
/* Layout */
max-w-7xl mx-auto px-4 sm:px-6 lg:px-8
min-h-screen flex flex-col

/* Navigation */
bg-white shadow-sm border-b border-gray-200
fixed top-0 left-0 right-0 z-50

/* Buttons */
bg-csc-green hover:bg-csc-light text-white px-4 py-2 rounded-md

/* Cards */
bg-white rounded-lg shadow-sm border border-gray-200

/* Forms */
w-full border border-gray-300 rounded-md px-3 py-2
focus:outline-none focus:ring-2 focus:ring-csc-green

/* Typography */
text-gray-900 (Überschriften)
text-gray-700 (Text)
text-gray-500 (Meta)
text-sm text-gray-600 (Beschreibungen)

/* Spacing */
space-y-4 (vertikaler Abstand)
space-x-4 (horizontaler Abstand)
p-4 (Padding)
m-4 (Margin)
```

---

## 8. Farbschema

```css
/* CSC Green (Hauptfarbe) */
--csc-green: #2D5A27;    /* Dunkelgrün - Primary */
--csc-light: #4A7C42;    /* Hellgrün - Hover */
--csc-accent: #7CB342;   /* Akzent */

/* Neutral */
--gray-50: #F9FAFB;      /* Hintergrund */
--gray-100: #F3F4F6;     /* Card-Hintergrund */
--gray-200: #E5E7EB;     /* Borders */
--gray-700: #374151;     /* Text */
--gray-900: #111827;     /* Überschriften */

/* Status */
--green-50: #F0FDF4;      /* Success-Hintergrund */
--red-50: #FEF2F2;       /* Error-Hintergrund */
--yellow-50: #FEFCE8;    /* Warning-Hintergrund */
```

---

## 9. JavaScript (HTMX + Alpine)

### HTMX für dynamische Updates
```html
<!-- Warenkorb-Count aktualisieren -->
<button hx-post="/cart/add/"
        hx-target="#cart-count"
        hx-swap="innerHTML">
    In den Warenkorb
</button>

<span id="cart-count">2</span>
```

### Alpine.js für Mobile Menu
```html
<div x-data="{ open: false }">
    <button @click="open = !open">Menü</button>
    <div x-show="open" @click.away="open = false">
        <!-- Mobile Menu -->
    </div>
</div>
```

---

## 10. Templates-Struktur

```
templates/
├── base.html                    # Base template (wie RedFlag)
├── includes/
│   ├── navigation.html          # Nav-Leiste
│   ├── footer.html              # Footer
│   └── messages.html            # Flash messages
├── home.html                    # Landing Page
├── shop/
│   ├── index.html               # Shop-Übersicht
│   ├── product_detail.html      # Produkt-Detail
│   └── cart.html                # Warenkorb
├── orders/
│   └── list.html                # Meine Bestellungen
├── members/
│   └── profile.html             # Profil
└── wallet/
    └── detail.html              # Guthaben
```

---

## Referenz: RedFlag Analyzer

**Zu kopieren:**
- ✅ Navigation-Struktur (Desktop + Mobile)
- ✅ Dropdown-Menüs
- ✅ Card-Layouts
- ✅ Form-Styling
- ✅ Button-Klassen
- ✅ Alert-Komponenten
- ✅ Responsive Breakpoints
- ✅ HTMX-Integration

**Anzupassen:**
- 🎨 Farben (rot → grün)
- 🏷️ Logo und Name
- 🎯 Icons (emoji)
- 📱 Spezifische CSC-Features

---

**Verwandte Dokumente:**
- [14-ui-wireframes.md](./14-ui-wireframes.md) - Wireframes
- [11-tech-stack.md](./11-tech-stack.md) - Tailwind, HTMX, Alpine