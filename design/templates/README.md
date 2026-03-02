# CSC Administration - Django Template Struktur

> Basierend auf RedFlag Analyzer Stack
> Django 5 + Tailwind CSS + Alpine.js + HTMX

---

## 📁 Template-Verzeichnisstruktur

```
templates/
├── base.html                    # Haupt-Template (Navigation, Footer)
├── dashboard.html               # Mitglied Dashboard
├── accounts/
│   ├── login.html              # Login-Seite
│   ├── register.html           # Registrierung
│   ├── profile.html            # Profil anzeigen
│   ├── profile_edit.html       # Profil bearbeiten
│   └── settings.html           # Einstellungen
├── members/
│   ├── list.html               # Mitglieder-Liste (Admin)
│   ├── detail.html             # Mitglied-Details
│   ├── create.html             # Neues Mitglied
│   └── edit.html               # Mitglied bearbeiten
├── orders/
│   ├── list.html               # Sorten-Liste (Bestellung)
│   ├── cart.html               # Warenkorb
│   ├── checkout.html           # Checkout
│   ├── history.html            # Bestellhistorie
│   └── detail.html             # Bestellung-Details
├── inventory/
│   ├── list.html               # Inventar-Übersicht
│   ├── create.html             # Neue Charge
│   └── detail.html             # Charge-Details
├── finance/
│   ├── dashboard.html          # Finanz-Übersicht
│   ├── transactions.html       # Transaktionen
│   └── deposit.html            # Guthaben aufladen
├── admin_panel/
│   ├── dashboard.html          # Admin Dashboard
│   ├── settings.html           # System-Einstellungen
│   └── logs.html               # Logs anzeigen
├── legal/
│   ├── datenschutz.html        # Datenschutzerklärung
│   ├── impressum.html          # Impressum
│   └── satzung.html            # Satzung
└── partials/
    ├── messages.html           # Flash Messages
    ├── pagination.html         # Pagination
    └── mobile_menu.html        # Mobile Menu
```

---

## 🎨 Design-System

### Farben
```css
--csc-green: #10B981          /* Primär - Actions, Links */
--csc-green-dark: #059669     /* Hover-States */
--csc-brown: #92400E          /* Akzent (optional) */
--gray-50: #F9FAFB            /* Hintergrund */
--gray-900: #111827           /* Text */
```

### Status-Farben
- ✅ **Aktiv**: `bg-green-100 text-green-800`
- ⏳ **Ausstehend**: `bg-yellow-100 text-yellow-800`
- 🆕 **Neu**: `bg-blue-100 text-blue-800`
- 🔴 **Gesperrt**: `bg-red-100 text-red-800`

### Breakpoints
- **Mobile**: < 768px (`md:`)
- **Tablet**: 768px - 1024px (`lg:`)
- **Desktop**: > 1024px

---

## 🧩 Wiederverwendbare Komponenten

### Navigation
```html
<!-- Desktop: Horizontales Menu -->
<!-- Mobile: Hamburger → Slide-out Menu -->
```

### Cards
```html
<div class="bg-white rounded-lg shadow p-6">
    <!-- Content -->
</div>
```

### Buttons
```html
<!-- Primary -->
<button class="bg-csc-green text-white px-4 py-2 rounded-md hover:bg-csc-green-dark">

<!-- Secondary -->
<button class="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300">

<!-- Danger -->
<button class="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700">
```

### Formulare
```html
<input class="block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-csc-green focus:border-csc-green">

<select class="block w-full pl-3 pr-10 py-2 border-gray-300 focus:ring-csc-green focus:border-csc-green rounded-md">
```

### Badges
```html
<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
    Aktiv
</span>
```

---

## 📱 Responsive Verhalten

### Mobile (< 768px)
- Navigation: Hamburger Menu (Slide-out von rechts)
- Logo: Gekürzt (nur "CSC")
- Grid: 1 Spalte
- Tabelle: Horizontales Scrollen
- Actions: Kompakte Buttons

### Desktop (> 768px)
- Navigation: Horizontales Menu
- Logo: Vollständig ("CSC Administration")
- Grid: 2-4 Spalten
- Tabelle: Volle Breite
- Actions: Dropdown Menu

---

## 🔧 JavaScript-Integration

### Alpine.js (Reactivity)
```html
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open">Content</div>
</div>
```

### HTMX (AJAX)
```html
<button hx-get="/api/data" hx-target="#result">
    Load Data
</button>
<div id="result"></div>
```

### Mobile Menu
```javascript
// Siehe base.html für Implementation
// Slide-out mit translate-x-full → translate-x-0
```

---

## 🚀 Erstellen neuer Templates

### 1. Template erstellen
```bash
touch templates/orders/confirmation.html
```

### 2. Base extenden
```html
{% extends "base.html" %}

{% block title %}Bestellung bestätigt - CSC Administration{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Content here -->
</div>
{% endblock %}
```

### 3. Responsive Grid verwenden
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- Cards -->
</div>
```

---

## 📋 Checkliste für neue Templates

- [ ] `{% extends "base.html" %}` am Anfang
- [ ] `{% block title %}` setzen
- [ ] `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8` Container verwenden
- [ ] Responsive Grid (`grid-cols-1 md:grid-cols-X`)
- [ ] Mobile-First Ansatz
- [ ] Status-Badges mit richtigen Farben
- [ ] Buttons mit `csc-green` Klasse
- [ ] Formulare mit Focus-Ring
- [ ] CSRF-Token in Forms: `{% csrf_token %}`

---

## 📝 Beispiel: Neues Template

```html
{% extends "base.html" %}

{% block title %}Neue Seite - CSC Administration{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="text-3xl font-bold text-gray-900 mb-8">Seitentitel</h1>
    
    <div class="bg-white rounded-lg shadow p-6">
        <p class="text-gray-600">Inhalt hier...</p>
        
        <div class="mt-4 flex space-x-2">
            <button class="bg-csc-green text-white px-4 py-2 rounded-md hover:bg-csc-green-dark">
                Speichern
            </button>
            <button class="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300">
                Abbrechen
            </button>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 🔗 Links

- **Tailwind CSS**: https://tailwindcss.com/
- **Alpine.js**: https://alpinejs.dev/
- **HTMX**: https://htmx.org/
- **Django Templates**: https://docs.djangoproject.com/en/5.0/topics/templates/

---

**Basierend auf**: RedFlag Analyzer Template-Struktur  
**Angepasst für**: CSC Administration  
**Erstellt**: 2. März 2026
