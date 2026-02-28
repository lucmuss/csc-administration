# Authentifizierung & Login

**Dokumentation:** Login-Methoden, Passwort-Stärke, Sicherheit

---

## Login-Optionen

Mitglied kann sich einloggen mit **einer** der drei Methoden:

### 1. Mitgliedsnummer
- • Eingabe: Mitgliedsnummer (z.B. "12345")
- • Passwort
- • Bevorzugte Methode für Mitglieder

### 2. E-Mail-Adresse
- • Eingabe: E-Mail
- • Passwort
- • Alternative für Mitglieder

### 3. Handynummer
- • Eingabe: +49 123 4567890
- • Passwort
- • Für mobile Nutzung

**Backend-Logik:**
```python
def authenticate_user(identifier, password):
    """
    Identifier kann sein:
    - Mitgliedsnummer (nur Zahlen)
    - E-Mail (enthält @)
    - Handynummer (startet mit + oder 0)
    """
    
    if identifier.isdigit():
        # Mitgliedsnummer
        member = Member.objects.get(member_number=identifier)
        user = member.user
    elif '@' in identifier:
        # E-Mail
        user = User.objects.get(email=identifier)
    else:
        # Handynummer
        member = Member.objects.get(phone=identifier)
        user = member.user
    
    # Passwort prüfen
    if user.check_password(password):
        return user
    return None
```

---

## Passwort-Stärke (aus BrainConnect)

### Frontend: JavaScript (mit Tailwind)

**Score-Berechnung:**
```javascript
function scorePassword(rawValue) {
  let score = 0;
  if (rawValue.length >= 8) score += 1;
  if (/[a-z]/.test(rawValue) && /[A-Z]/.test(rawValue)) score += 1;
  if (/\d/.test(rawValue)) score += 1;
  if (/[^A-Za-z0-9]/.test(rawValue)) score += 1;
  if (rawValue.length >= 12) score += 1;
  return score;
}

function getStrengthState(score) {
  if (score <= 1) return { 
    bars: 1, 
    label: "Passwort-Stärke: schwach", 
    className: "bg-rose-500" 
  };
  if (score === 2) return { 
    bars: 2, 
    label: "Passwort-Stärke: mittel", 
    className: "bg-amber-500" 
  };
  if (score === 3) return { 
    bars: 3, 
    label: "Passwort-Stärke: gut", 
    className: "bg-sky-500" 
  };
  if (score === 4) return { 
    bars: 4, 
    label: "Passwort-Stärke: stark", 
    className: "bg-emerald-500" 
  };
  return { 
    bars: 4, 
    label: "Passwort-Stärke: sehr stark", 
    className: "bg-emerald-600" 
  };
}
```

**HTML-Template:**
```html
<!-- Passwort-Feld mit Stärke-Anzeige -->
<div class="space-y-2">
  <label for="password">Passwort</label>
  <input 
    type="password" 
    id="password" 
    name="password"
    class="w-full border rounded px-3 py-2"
    placeholder="Passwort eingeben"
  >
  
  <!-- Stärke-Anzeige -->
  <div data-password-strength data-password-input="password">
    <!-- 4 Balken -->
    <div class="flex gap-1 h-2 mt-2">
      <div data-strength-bar class="flex-1 bg-slate-200 rounded"></div>
      <div data-strength-bar class="flex-1 bg-slate-200 rounded"></div>
      <div data-strength-bar class="flex-1 bg-slate-200 rounded"></div>
      <div data-strength-bar class="flex-1 bg-slate-200 rounded"></div>
    </div>
    <!-- Label -->
    <p data-strength-label class="text-sm text-gray-600 mt-1">
      Mindestens 8 Zeichen, Groß-/Kleinbuchstaben, Zahl und Symbol.
    </p>
  </div>
</div>
```

**Farben (Tailwind):**
- • 0-1: `bg-rose-500` (Rot) - Schwach
- • 2: `bg-amber-500` (Orange) - Mittel
- • 3: `bg-sky-500` (Blau) - Gut
- • 4: `bg-emerald-500` (Grün) - Stark
- • 5: `bg-emerald-600` (Dunkelgrün) - Sehr stark

### Backend: Django Validation

```python
from django.core.exceptions import ValidationError
import re

def validate_password_strength(password):
    """Server-seitige Passwort-Validierung"""
    
    if len(password) < 8:
        raise ValidationError("Passwort muss mindestens 8 Zeichen lang sein.")
    
    if not re.search(r'[a-z]', password) or not re.search(r'[A-Z]', password):
        raise ValidationError("Passwort muss Groß- und Kleinbuchstaben enthalten.")
    
    if not re.search(r'\d', password):
        raise ValidationError("Passwort muss mindestens eine Zahl enthalten.")
    
    if not re.search(r'[^A-Za-z0-9]', password):
        raise ValidationError("Passwort muss mindestens ein Sonderzeichen enthalten.")
    
    return True
```

---

## Passwort-Setzen bei Registrierung

### Flow

```
1. Mitglied beantragt Mitgliedschaft
        ↓
2. Vorstand genehmigt
        ↓
3. System generiert temporäres Passwort
   ODER: Einladungs-Link zum Setzen
        ↓
4. E-Mail an Mitglied:
   "Setze dein Passwort"
        ↓
5. Mitglied setzt Passwort
   (mit Stärke-Prüfung)
        ↓
6. Erster Login möglich
```

### E-Mail: Passwort setzen
```
Betreff: Setze dein Passwort für [Club-Name]

Hallo [Vorname],

deine Mitgliedschaft wurde genehmigt!

Um dich einzuloggen, musst du zuerst ein Passwort setzen.

[Passwort setzen →]

Dieser Link ist 24 Stunden gültig.

Deine Login-Daten:
• Mitgliedsnummer: [NUMMER]
• Oder E-Mail: [EMAIL]
• Oder Handynummer: [TELEFON]

Nach dem Setzen des Passworts kannst du dich einloggen.
```

---

## Passwort-Reset (Vergessen)

### Flow

```
1. Mitglied klickt "Passwort vergessen"
        ↓
2. Eingabe: Mitgliedsnummer / E-Mail / Telefon
        ↓
3. System sendet Reset-Link an E-Mail
        ↓
4. Mitglied klickt Link
        ↓
5. Neues Passwort setzen (mit Stärke-Prüfung)
        ↓
6. Login mit neuem Passwort
```

### Reset-Seite
```html
<h1>Passwort zurücksetzen</h1>

<form method="post">
  <label> Mitgliedsnummer, E-Mail oder Handynummer</label>
  <input type="text" name="identifier" required>
  
  <button type="submit">Reset-Link senden</button>
</form>
```

### Reset-E-Mail
```
Betreff: Passwort zurücksetzen für [Club-Name]

Hallo,

du hast angefordert, dein Passwort zurückzusetzen.

Falls du das warst, klicke hier:
[Passwort zurücksetzen →]

Falls nicht, ignoriere diese E-Mail einfach.

Der Link ist 1 Stunde gültig.
```

---

## Sicherheits-Features

### 1. Argon2 Passwort-Hashing
```python
# settings.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
```

### 2. Login-Versuche limitieren
```python
# django-ratelimit
@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # Max 5 Login-Versuche pro Minute
    pass
```

### 3. Session-Management
- • Sessions nach 2 Stunden Inaktivität ablaufen
- • Bei Passwort-Änderung: alle anderen Sessions beenden
- • "Angemeldet bleiben" Option (30 Tage)

### 4. 2FA (Optional später)
- • TOTP (Authenticator App)
- • SMS (kostenintensiv)
- • FIDO2/WebAuthn (YubiKey)

---

## Login-Seite (UI)

### Einfaches Design (Tailwind)
```html
<div class="min-h-screen flex items-center justify-center bg-gray-100">
  <div class="bg-white p-8 rounded shadow-md w-full max-w-md">
    <h1 class="text-2xl font-bold mb-6 text-center">🌿 [Club-Name]</h1>
    
    <form method="post" class="space-y-4">
      <div>
        <label class="block text-sm font-medium mb-1">
          Mitgliedsnummer, E-Mail oder Handynummer
        </label>
        <input 
          type="text" 
          name="identifier"
          class="w-full border rounded px-3 py-2"
          placeholder="z.B. 12345"
          required
        >
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-1">Passwort</label>
        <input 
          type="password" 
          name="password"
          class="w-full border rounded px-3 py-2"
          required
        >
      </div>
      
      <button 
        type="submit"
        class="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
      >
        Anmelden
      </button>
    </form>
    
    <div class="mt-4 text-center text-sm">
      <a href="/passwort-vergessen/" class="text-green-600 hover:underline">
        Passwort vergessen?
      </a>
    </div>
  </div>
</div>
```

---

## User Model Erweiterung

```python
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Erweiterter User mit Telefonnummer"""
    
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Login mit E-Mail erlauben
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'  # Wir ändern das für CSC
```

### Custom Authentication Backend
```python
class MemberAuthBackend:
    """Erlaubt Login mit Mitgliedsnummer, E-Mail oder Telefon"""
    
    def authenticate(self, request, identifier=None, password=None):
        try:
            # Versuche als Mitgliedsnummer
            if identifier.isdigit():
                member = Member.objects.get(member_number=identifier)
                user = member.user
            # Versuche als E-Mail
            elif '@' in identifier:
                user = User.objects.get(email=identifier)
            # Versuche als Telefon
            else:
                member = Member.objects.get(phone=identifier)
                user = member.user
            
            if user.check_password(password):
                return user
        except (Member.DoesNotExist, User.DoesNotExist):
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
```

---

## Nächste Schritte

1. [ ] Custom User Model erstellen
2. [ ] Authentication Backend implementieren
3. [ ] Login-View erstellen
4. [ ] Passwort-Stärke-JavaScript einbauen
5. [ ] Passwort-Reset-Flow implementieren
6. [ ] Session-Management konfigurieren

---

**Verwandte Dokumente:**
- [16-mitgliedschafts-workflow.md](./16-mitgliedschafts-workflow.md) - Erst-Login nach Genehmigung
- [12-security-requirements.md](./12-security-requirements.md) - Allgemeine Sicherheit
- [11-tech-stack.md](./11-tech-stack.md) - Argon2, django-allauth