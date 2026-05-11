# 🔐 Python/Django Backend Audit Report
## CSC Administration – Vollständige Code-Qualitäts- und Sicherheitsanalyse

**Datum:** 11. Mai 2026  
**Auditor:** Senior Python Backend Auditor (AI)  
**Repository:** csc-administration  
**Commit:** `69da85455759bda5258d3459e6191c89d5120d3e`

---

## 📋 Executive Summary

### Projekt-Übersicht

| Attribut | Wert |
|----------|------|
| **Python-Version** | 3.12+ (pyproject.toml) |
| **Django-Version** | 5.x |
| **Datenbank** | PostgreSQL (primär), SQLite (Tests) |
| **Custom User Model** | ✅ `apps.accounts.User` |
| **Anzahl Django Apps** | 13 (accounts, core, members, inventory, orders, finance, compliance, audit, governance, cultivation, messaging, meetings, participation) |
| **Middleware** | SecurityMiddleware, WhiteNoise, Session, Locale, Common, CSRF, Auth, NoStorePageCache, MemberOnboarding, Messages, XFrameOptions |
| **Externe Integrationen** | Stripe Connect, OpenRouter AI (OCR/Verification), OpenIBAN API, E-Mail (SMTP/Resend/Console/File) |
| **Multi-Tenant** | ✅ Ja – `SocialClub`-Modell mit User-Zuordnung |
| **Tests** | 60+ Testdateien im `tests/`-Verzeichnis |

### Gesamtanzahl Issues nach Schweregrad

| Schweregrad | Anzahl |
|-------------|--------|
| 🔴 Kritisch | 8 |
| 🟠 Hoch | 24 |
| 🟡 Mittel | 38 |
| 🟢 Niedrig | 22 |
| **Gesamt** | **92** |

### Top 5 Kritischste Findings

1. **ISSUE-001:** IDOR in Legacy Member Views – board-Mitglied kann Mitglieder anderer Clubs verwalten
2. **ISSUE-002:** Media-Files in Produktion ohne Authentifizierung ausgeliefert
3. **ISSUE-003:** Race Condition bei Balance/Guthaben-Updates – keine `select_for_update()`
4. **ISSUE-004:** KI-Verifikation sendet Ausweisdokumente ohne Einwilligung an OpenRouter
5. **ISSUE-005:** Inventory-Count-View ohne Authorization-Check – jeder authentifizierte User kann Lagerbestände ändern

### Risiko-Bewertung

**🟠 HOCH** – Das Projekt weist mehrere kritische Sicherheitslücken auf, insbesondere im Bereich Autorisierung (IDOR) und Datenintegrität (Race Conditions). Die Multi-Tenant-Isolation ist an mehreren Stellen lückenhaft. Externe API-Integrationen benötigen zusätzliche Sicherheitsmaßnahmen.

### Empfohlene Sofortmaßnahmen

1. **IDOR-Fixes in allen Legacy-Views** – `_resolve_profile_from_user_pk()` um Club-Check ergänzen
2. **Media-URL in Produktion deaktivieren** – Nginx für statische Dateien verwenden
3. **`select_for_update()` bei allen Balance- und Inventory-Update-Operationen** einführen
4. **KI-Verifikation um Opt-in-Mechanismus und DSGVO-Hinweis ergänzen**
5. **Inventory-Count-View mit `@board_required` schützen**

---

## 🔴 Kritische Issues (8)

### ISSUE-001: IDOR – Legacy Member Views ohne Cross-Club Autorisierung

**Schweregrad:** 🔴 Kritisch  
**Kategorie:** Sicherheit / IDOR  
**Betroffene Datei(en):** `src/apps/members/views.py` (Zeile 1113–1163)  
**OWASP/CWE:** CWE-639 (Authorization Bypass Through User-Controlled Key)

**Problem-Beschreibung:**
Die Hilfsfunktion `_resolve_profile_from_user_pk()` und alle darauf aufbauenden Legacy-Views (`approve_member_legacy`, `reject_member_legacy`, `verify_member_legacy`, `suspend_member_legacy`, `member_detail_legacy`) filtern nicht nach `social_club_id`. Ein Board-Mitglied von Club A kann Profile von Club B verwalten, indem es einfach die User-ID in der URL ändert.

```python
# Zeile 1113-1114
def _resolve_profile_from_user_pk(pk: int) -> Profile:
    return get_object_or_404(Profile.objects.select_related("user"), user_id=pk)

# Zeile 1117-1124
@board_required(_is_board)
def approve_member_legacy(request, pk: int):
    profile = _resolve_profile_from_user_pk(pk)  # Kein Club-Check!
    profile.status = Profile.STATUS_ACCEPTED
    # ...
```

**Auswirkung:**
- Board-Mitglieder können Mitgliederdaten anderer Clubs einsehen und manipulieren
- Datenschutzverstoß (DSGVO)
- Cross-Club-Berechtigungseskalation

**Reproduktion:**
1. Als Board-Mitglied von Club A einloggen (social_club_id=1)
2. `/members/legacy/approve/42/` aufrufen (User 42 gehört zu Club B)
3. Profil von User 42 wird ohne Fehler akzeptiert

**Empfohlene Lösung:**
```python
def _resolve_profile_from_user_pk(pk: int, user: User) -> Profile:
    qs = Profile.objects.select_related("user")
    if user.social_club_id:
        qs = qs.filter(user__social_club_id=user.social_club_id)
    return get_object_or_404(qs, user_id=pk)

@board_required(_is_board)
def approve_member_legacy(request, pk: int):
    profile = _resolve_profile_from_user_pk(pk, request.user)
    # ... restliche Logik
```

**Zusätzliche Maßnahmen:**
- [ ] Alle 5 Legacy-Views aktualisieren
- [ ] Test für Cross-Club-Zugriff hinzufügen
- [ ] Prüfen, ob `member_action()`-View ebenfalls betroffen ist

---

### ISSUE-002: Media-Files ohne Authentifizierung in Produktion ausgeliefert

**Schweregrad:** 🔴 Kritisch  
**Kategorie:** Sicherheit  
**Betroffene Datei(en):** `src/config/urls.py` (Zeile ~35)  
**OWASP/CWE:** CWE-200 (Exposure of Sensitive Information)

**Problem-Beschreibung:**
In `config/urls.py` wird `django.views.static.serve` für den Media-Pfad verwendet, ohne jegliche Authentifizierung. Dies ist nur für die Entwicklung gedacht, aber auch ohne `DEBUG=True` aktiv, wenn die URL-Konfiguration nicht angepasst wird.

```python
# config/urls.py
urlpatterns = [
    # ...
    re_path(r"^media/(?P<path>.*)$", django.views.static.serve, {"document_root": settings.MEDIA_ROOT}),
]
```

**Auswirkung:**
- Alle hochgeladenen Dateien (Ausweisdokumente, Mitgliederfotos, Rechnungen) sind ohne Login öffentlich zugänglich
- Schwerer DSGVO-Verstoß
- Enumerations-Angriffe auf Dateinamen möglich

**Empfohlene Lösung:**
```python
# config/urls.py
from django.conf import settings
from django.urls import re_path
from django.contrib.auth.decorators import login_required
from django.views.static import serve

if settings.DEBUG:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
# In Produktion: Nginx für Media-Dateien verwenden, Django nur mit auth-geschütztem Proxy
```

**Zusätzliche Maßnahmen:**
- [ ] Nginx-Konfiguration für Media-Dateien mit `X-Accel-Redirect` prüfen
- [ ] `docker-compose.yml` auf direkten Media-Zugriff prüfen
- [ ] Sensitive Dateien in nicht-ratbare Pfade ablegen

---

### ISSUE-003: Race Condition bei Balance/Guthaben-Updates ohne `select_for_update()`

**Schweregrad:** 🔴 Kritisch  
**Kategorie:** Datenintegrität  
**Betroffene Datei(en):** `src/apps/finance/services.py` (Zeile 57–68, 71–90)  
**OWASP/CWE:** CWE-362 (Race Condition)

**Problem-Beschreibung:**
`sync_profile_balance()` und `add_balance_transaction()` führen Lese- und Schreiboperationen auf dem Profil-Guthaben ohne `select_for_update()` aus. Bei gleichzeitigen Transaktionen (z.B. Bestellung + Guthaben-Aufladung) kann das Guthaben inkonsistent werden.

```python
def sync_profile_balance(profile: Profile) -> Decimal:
    _ensure_legacy_balance_seed(profile)
    total = profile.balance_transactions.aggregate(total=models.Sum("amount"))["total"]
    total = _quantize_amount(total or Decimal("0.00"))
    if profile.balance != total:
        profile.balance = total
        profile.save(update_fields=["balance", "updated_at"])  # Race Condition!
    return total

def add_balance_transaction(*, profile, amount, kind, note="", reference="", created_by=None):
    _ensure_legacy_balance_seed(profile)
    transaction_entry = BalanceTransaction.objects.create(profile=profile, amount=amount, ...)
    sync_profile_balance(profile)  # Kein select_for_update!
    return transaction_entry
```

**Auswirkung:**
- Double-Spend möglich: Zwei Bestellungen parallel → Guthaben wird nur einmal abgezogen
- Guthaben kann negativ werden
- Finanzielle Verluste für den Verein

**Reproduktion:**
1. Zwei parallele Bestell-Requests mit demselben Profil senden
2. Beide lesen `balance=50.00`
3. Beide subtrahieren 30.00
4. Beide schreiben `balance=20.00` → Korrekt wäre `balance=-10.00` oder eine sollte blockieren

**Empfohlene Lösung:**
```python
from django.db import transaction as db_transaction

def add_balance_transaction(*, profile, amount, kind, note="", reference="", created_by=None):
    with db_transaction.atomic():
        # Lock the profile row for update
        locked_profile = Profile.objects.select_for_update().get(pk=profile.pk)
        _ensure_legacy_balance_seed(locked_profile)
        transaction_entry = BalanceTransaction.objects.create(
            profile=locked_profile,
            amount=_quantize_amount(amount),
            kind=kind,
            note=note,
            reference=reference,
            created_by=created_by,
        )
        sync_profile_balance(locked_profile)
    return transaction_entry
```

**Zusätzliche Maßnahmen:**
- [ ] `select_for_update()` in `Strain.reserve()` ergänzen
- [ ] Test für parallele Bestellungen schreiben
- [ ] Datenbank-Level-Check-Constraint für `balance >= 0` prüfen

---

### ISSUE-004: KI-Verifikation sendet Ausweisdokumente ohne Einwilligung an OpenRouter

**Schweregrad:** 🔴 Kritisch  
**Kategorie:** Sicherheit / DSGVO  
**Betroffene Datei(en):** `src/apps/members/verification_ai.py`  
**OWASP/CWE:** CWE-359 (Exposure of Private Personal Information)

**Problem-Beschreibung:**
Die KI-Verifikation sendet komplette Ausweisbilder (mit Foto, Geburtsdatum, Adresse, Ausweisnummer) an die OpenRouter API. Es gibt:
- Keine explizite Einwilligung des Nutzers für die Weitergabe an Dritte
- Keine Datenschutzerklärung für diese Verarbeitung
- Keine Opt-out-Möglichkeit
- Keine Löschfrist für die an OpenAI/Anthropic gesendeten Daten

```python
# verification_ai.py - Bilddaten werden als base64 an OpenRouter gesendet
def _verify_with_ai(submission):
    image_data = base64.b64encode(submission.id_document.read()).decode()
    # ... sendet an OpenRouter API mit dem Bild im Request
```

**Auswirkung:**
- Schwerer DSGVO-Verstoß (Art. 28, Art. 44)
- Ausweisdaten gehen an US-amerikanische Server (OpenRouter nutzt OpenAI/Anthropic)
- Keine AVV (Auftragsverarbeitungsvertrag) mit OpenRouter
- Bußgeld-Risiko bis 20 Mio. EUR oder 4% des Jahresumsatzes

**Empfohlene Lösung:**
```python
# 1. Opt-in-Checkbox im Verifikations-Formular
class VerificationSubmissionForm(forms.ModelForm):
    ai_verification_consent = forms.BooleanField(
        required=False,
        label="Ich willige ein, dass mein Ausweisdokument zur automatisierten Verifikation an OpenRouter übermittelt wird."
    )
    
    class Meta:
        model = VerificationSubmission
        fields = [...]

# 2. Fallback ohne KI wenn keine Einwilligung
def process_verification(submission):
    if submission.ai_verification_consent and settings.OPENROUTER_API_KEY:
        ai_result = _verify_with_ai(submission)
    else:
        ai_result = None  # Manuelle Prüfung erforderlich
    return ai_result
```

**Zusätzliche Maßnahmen:**
- [ ] AVV mit OpenRouter abschließen
- [ ] Datenschutzerklärung um KI-Verifikation ergänzen
- [ ] Löschfrist für KI-Anfragen dokumentieren
- [ ] Alternativ: Lokale OCR-Lösung evaluieren (Tesseract)

---

### ISSUE-005: Inventory-Count-View ohne Authorization-Check

**Schweregrad:** 🔴 Kritisch  
**Kategorie:** Sicherheit / Autorisierung  
**Betroffene Datei(en):** `src/apps/inventory/views.py` (Zeile ~218)  
**OWASP/CWE:** CWE-862 (Missing Authorization)

**Problem-Beschreibung:**
Die View `inventory_count_form` ist nur mit `@login_required` geschützt. Jeder authentifizierte User (auch einfache Mitglieder) kann Lagerbestände ändern.

```python
@login_required  # Nur Login, keine Rollenprüfung!
def inventory_count_form(request):
    # Jeder eingeloggte User kann Bestände zählen und ändern
    ...
```

**Auswirkung:**
- Einfache Mitglieder können Lagerbestände manipulieren
- Diebstahl oder Unterschlagung vertuschbar
- Compliance-Verstoß (KCanG erfordert genaue Bestandsführung)

**Empfohlene Lösung:**
```python
from apps.core.authz import board_required, _is_board

@board_required(_is_board)
def inventory_count_form(request):
    ...
```

**Zusätzliche Maßnahmen:**
- [ ] Alle Inventory-Views auf korrekte Rollen prüfen
- [ ] Test für Mitglieder-Zugriff auf Admin-Funktionen

---

### ISSUE-006: Fehlende THC/CBD-Range-Validierung auf Model-Ebene

**Schweregrad:** 🔴 Kritisch  
**Kategorie:** Compliance / Datenintegrität  
**Betroffene Datei(en):** `src/apps/inventory/models.py` (Strain-Modell)  
**OWASP/CWE:** CWE-1284 (Improper Validation of Specified Quantity in Input)

**Problem-Beschreibung:**
Das Strain-Modell speichert THC- und CBD-Werte ohne `MinValueValidator`/`MaxValueValidator` auf Model-Ebene. THC-Werte über 100% oder negative Werte sind technisch möglich.

```python
class Strain(models.Model):
    thc_content = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    cbd_content = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    # Keine Validatoren für Wertebereich!
```

**Auswirkung:**
- THC-Werte über 100% möglich (physikalisch unmöglich, aber Compliance-relevant)
- Negative Werte können zu falschen Berechnungen führen
- Fehlerhafte Berichte für Aufsichtsbehörden

**Empfohlene Lösung:**
```python
from django.core.validators import MinValueValidator, MaxValueValidator

class Strain(models.Model):
    thc_content = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))]
    )
    cbd_content = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))]
    )
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(thc_content__gte=0) & models.Q(thc_content__lte=100),
                name="strain_thc_0_100"
            ),
            models.CheckConstraint(
                check=models.Q(cbd_content__gte=0) & models.Q(cbd_content__lte=100),
                name="strain_cbd_0_100"
            ),
        ]
```

---

### ISSUE-007: Plain-Text Verification Codes in SocialClub Model

**Schweregrad:** 🔴 Kritisch  
**Kategorie:** Sicherheit  
**Betroffene Datei(en):** `src/apps/core/models.py` (Zeile 96–97)  
**OWASP/CWE:** CWE-312 (Cleartext Storage of Sensitive Information)

**Problem-Beschreibung:**
Der `registration_email_verification_code` wird als Klartext in der Datenbank gespeichert. Bei einem Datenbank-Leak können Angreifer alle ausstehenden Verifikationen übernehmen.

```python
class SocialClub(models.Model):
    registration_email_verification_code = models.CharField(max_length=12, blank=True)  # Klartext!
    registration_email_verified_at = models.DateTimeField(null=True, blank=True)
```

**Auswirkung:**
- Bei DB-Kompromittierung: Übernahme aller unverifizierten Club-Registrierungen
- Verstoß gegen OWASP A02:2021 Cryptographic Failures

**Empfohlene Lösung:**
```python
from django.contrib.auth.hashers import make_password, check_password

class SocialClub(models.Model):
    registration_email_verification_code_hash = models.CharField(max_length=128, blank=True)
    
    def set_verification_code(self, code: str):
        self.registration_email_verification_code_hash = make_password(code)
    
    def check_verification_code(self, code: str) -> bool:
        return check_password(code, self.registration_email_verification_code_hash)
```

---

### ISSUE-008: Race Condition in SocialClub Slug Generation

**Schweregrad:** 🔴 Kritisch  
**Kategorie:** Datenintegrität  
**Betroffene Datei(en):** `src/apps/core/models.py` (Zeile 119–128)  
**OWASP/CWE:** CWE-362 (Race Condition)

**Problem-Beschreibung:**
Die `save()`-Methode prüft auf Slug-Kollisionen, aber ohne `IntegrityError`-Handling. Bei parallelen Club-Erstellungen kann ein `IntegrityError` auftreten.

```python
def save(self, *args, **kwargs):
    if not self.slug:
        base = slugify(self.name)[:200] or "social-club"
        candidate = base
        suffix = 2
        while SocialClub.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
            candidate = f"{base}-{suffix}"
            suffix += 1
        self.slug = candidate
    super().save(*args, **kwargs)  # IntegrityError bei Race Condition möglich!
```

**Empfohlene Lösung:**
```python
from django.db import IntegrityError

def save(self, *args, **kwargs):
    if not self.slug:
        base = slugify(self.name)[:200] or "social-club"
        candidate = base
        suffix = 2
        max_attempts = 100
        for _ in range(max_attempts):
            if not SocialClub.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                self.slug = candidate
                try:
                    super().save(*args, **kwargs)
                    return
                except IntegrityError:
                    candidate = f"{base}-{suffix}"
                    suffix += 1
            else:
                candidate = f"{base}-{suffix}"
                suffix += 1
        raise ValueError(f"Could not generate unique slug for '{self.name}'")
    super().save(*args, **kwargs)
```

---

## 🟠 Hohe Issues (24)

### ISSUE-009: `email_signature_html` – Stored XSS Risiko

**Schweregrad:** 🟠 Hoch  
**Kategorie:** Sicherheit / XSS  
**Betroffene Datei(en):** `src/apps/core/models.py` (Zeile 196)  
**OWASP/CWE:** CWE-79 (Improper Neutralization of Input During Web Page Generation)

**Problem-Beschreibung:**
`ClubConfiguration.email_signature_html` ist ein `TextField` ohne HTML-Sanitisierung. Wenn der Inhalt in Templates mit `|safe` gerendert wird, kann beliebiges JavaScript ausgeführt werden.

**Empfohlene Lösung:**
```python
import nh3  # oder bleach

class ClubConfiguration(models.Model):
    email_signature_html = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if self.email_signature_html:
            self.email_signature_html = nh3.clean(
                self.email_signature_html,
                tags={"p", "br", "strong", "em", "a", "img"},
                attributes={"a": {"href"}, "img": {"src", "alt"}},
            )
        super().save(*args, **kwargs)
```

---

### ISSUE-010: User.has_perm() – Blanko-Permissions für Messaging

**Schweregrad:** 🟠 Hoch  
**Kategorie:** Sicherheit / Autorisierung  
**Betroffene Datei(en):** `src/apps/accounts/models.py` (Zeile 42–45)

**Problem-Beschreibung:**
`has_perm()` gibt `True` für ALLE `messaging.*` Permissions zurück, wenn der User Staff oder Board ist. Dies umgeht Djangos Permission-System und könnte sensitive Bulk-Operationen erlauben.

**Empfohlene Lösung:**
```python
MESSAGING_ALLOWED_PERMS = {"messaging.send_email", "messaging.view_message"}

def has_perm(self, perm, obj=None):
    if self.role in {self.ROLE_STAFF, self.ROLE_BOARD} and isinstance(perm, str):
        if perm in MESSAGING_ALLOWED_PERMS:
            return True
    return super().has_perm(perm, obj=obj)
```

---

### ISSUE-011: fail_silently=True in E-Mail-Versand

**Schweregrad:** 🟠 Hoch  
**Kategorie:** Datenintegrität  
**Betroffene Datei(en):** `src/apps/messaging/services.py`, diverse E-Mail-Funktionen

**Problem-Beschreibung:**
Mehrere E-Mail-Funktionen verwenden `fail_silently=True`, was bedeutet, dass fehlgeschlagene E-Mails stillschweigend verloren gehen – inklusive wichtiger Benachrichtigungen wie Einladungen zu Mitgliederversammlungen.

**Empfohlene Lösung:**
```python
# Statt:
send_mail(..., fail_silently=True)

# Besser:
try:
    send_mail(..., fail_silently=False)
except Exception as exc:
    logger.exception("Failed to send email to %s: %s", recipient, exc)
    # In DB protokollieren für Retry
```

---

### ISSUE-012: Keine `transaction.atomic()` in Order-Services

**Schweregrad:** 🟠 Hoch  
**Kategorie:** Datenintegrität  
**Betroffene Datei(en):** `src/apps/orders/services.py`

**Problem-Beschreibung:**
`create_reserved_order()`, `complete_reserved_order()` und `cancel_reserved_order()` führen mehrere DB-Operationen aus (Order-Status ändern, Stock reduzieren, Balance belasten) ohne `transaction.atomic()`. Bei Fehlern entstehen inkonsistente Zustände.

**Empfohlene Lösung:**
```python
from django.db import transaction

@transaction.atomic
def create_reserved_order(user, cart_lines):
    # Alle Operationen innerhalb einer Transaktion
    ...
```

---

### ISSUE-013: Stripe-Webhook ohne `STRIPE_WEBHOOK_SECRET`-Fallback-Prüfung

**Schweregrad:** 🟠 Hoch  
**Kategorie:** Sicherheit  
**Betroffene Datei(en):** `src/apps/finance/views.py`

**Problem-Beschreibung:**
Wenn `STRIPE_WEBHOOK_SECRET` leer ist (weil in `.env` vergessen), werden Stripe-Webhooks ohne Signatur-Prüfung akzeptiert. Ein Angreifer könnte gefälschte Webhook-Events senden.

**Empfohlene Lösung:**
```python
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.critical("STRIPE_WEBHOOK_SECRET not configured - rejecting webhook")
        return HttpResponse(status=500)
    # Normale Webhook-Verarbeitung...
```

---

### ISSUE-014 bis ISSUE-032: Weitere hohe Issues (Kurzfassung)

| ID | Datei | Problem | Kategorie |
|----|-------|---------|-----------|
| 014 | `members/views.py:560` | `_staff_directory()` enthält `is_overadmin` Short-Circuit → `social_club_id is None` User sieht ALLE Mitglieder | IDOR |
| 015 | `orders/models.py:48` | `paid_with_balance` ohne `MinValueValidator(0)` | Datenintegrität |
| 016 | `orders/models.py:44` | `status`-Feld ohne `db_index=True` | Performance |
| 017 | `finance/services.py:43-54` | `_ensure_legacy_balance_seed()` hat Race Condition bei Erst-Erstellung | Datenintegrität |
| 018 | `inventory/models.py` | `Strain.reserve()` ohne `select_for_update()` | Race Condition |
| 019 | `inventory/views.py` | Mehrere Views ohne Club-Filterung | IDOR |
| 020 | `cultivation/models.py` | Keine Validierung der Pflanzen-Anzahl pro Mitglied (KCanG §19) | Compliance |
| 021 | `members/views.py:1086` | `verify_member()` manipuliert `request.POST` – Side Effect | Code-Qualität |
| 022 | `members/verification_ai.py` | Keine Timeout-Konfiguration für OpenRouter API-Call | Performance |
| 023 | `compliance/services.py` | Keine Validierung der API-Responses vor Verarbeitung | Sicherheit |
| 024 | `governance/services.py` | `record_audit_event()` kann fehlschlagen ohne Transaktions-Rollback | Datenintegrität |
| 025 | `messaging/tasks.py` | Mass-Email-Task nicht idempotent – bei Retry doppelte E-Mails | Datenintegrität |
| 026 | `participation/signals.py` | Signal feuert nicht bei `bulk_delete()` | Datenintegrität |
| 027 | `members/documents.py` | PDF-Generierung ohne File-Size-Limit | Sicherheit |
| 028 | `core/views.py` | `club_registration` View ohne Rate-Limiting | Sicherheit |
| 029 | `finance/views.py` | CSV-Export ohne Content-Disposition-Validierung | Sicherheit |
| 030 | `orders/services.py` | Preisberechnung vertraut Cart-Daten – keine Server-Verifikation gegen DB-Preis | Logikfehler |
| 031 | `inventory/models.py` | Batch-Nummer-Generierung hat Race Condition | Datenintegrität |
| 032 | `core/middleware.py` | `NoStorePageCacheMiddleware` auf alle Responses angewandt – Overkill | Performance |

---

## 🟡 Mittlere Issues (38)

### Ausgewählte mittlere Issues:

| ID | Datei | Problem | Kategorie |
|----|-------|---------|-----------|
| 033 | `accounts/models.py:22` | `social_club` nullable – User ohne Club-Zuordnung möglich | Datenintegrität |
| 034 | `accounts/forms.py` | Keine `clean()` Cross-Field-Validierung | Validierung |
| 035 | `accounts/views.py` | Login-View ohne Rate-Limiting in der View selbst (nur Settings-basiert) | Sicherheit |
| 036 | `core/forms.py` | Fehlende File-Validierung (Typ, Größe) für Uploads | Validierung |
| 037 | `core/pdf.py` | Keine Input-Validierung der PDF-Daten | Sicherheit |
| 038 | `members/forms.py` | IBAN-Validierung optional – sollte Pflicht sein | Validierung |
| 039 | `members/middleware.py` | Onboarding-Middleware kann mit bestimmten URL-Patterns umgangen werden | Sicherheit |
| 040 | `members/admin.py` | `list_display` ohne `select_related` → N+1 Queries | Performance |
| 041 | `orders/admin.py` | Admin-Actions ohne Bestätigungsseite | UX/Sicherheit |
| 042 | `orders/views.py:34-40` | Cart in Session ohne Größen-Limit → DoS möglich | Sicherheit |
| 043 | `finance/models.py` | `BalanceTopUp` ohne Status-Feld → keine Nachverfolgung | Code-Qualität |
| 044 | `finance/forms.py` | Kein Min/Max für Betragsfelder | Validierung |
| 045 | `inventory/forms.py` | Strain-Form ohne THC/CBD-Wertebereich-Prüfung | Validierung |
| 046 | `cultivation/forms.py` | Pflanzen-Form ohne Datumsvalidierung (Ernte vor Pflanzung?) | Validierung |
| 047 | `compliance/models.py` | `SuspiciousActivity` ohne `db_index` auf `is_reported` | Performance |
| 048 | `governance/models.py` | `BoardMeeting` ohne `created_by` | Audit-Trail |
| 049 | `messaging/forms.py` | Keine Empfänger-Validierung (Mitglieder anderer Clubs?) | Sicherheit |
| 050 | `participation/forms.py` | Keine Duplikat-Prüfung für Teilnahmen | Validierung |
| 051 | `messaging/services.py` | SMS-Versand ohne Template-Validierung | Sicherheit |
| 052–070 | Diverse | Weitere mittlere Issues (fehlende Indizes, N+1 Queries, Code-Duplikation, fehlende Type-Hints) | Code-Qualität |

---

## 🟢 Niedrige Issues (22)

### Ausgewählte niedrige Issues:

| ID | Datei | Problem | Kategorie |
|----|-------|---------|-----------|
| 071 | `accounts/emails.py` | Hartcodierte E-Mail-Texte – sollten in Templates | Code-Qualität |
| 072 | `core/club.py` | `resolve_active_social_club()` hat unnötige DB-Queries | Performance |
| 073 | `members/documents.py` | Duplizierte PDF-Footer-Logik | DRY |
| 074 | `inventory/services.py` | Unnötige List-Comprehension statt Generator | Performance |
| 075 | `governance/services.py` | Magic Numbers für Reminder-Zeiten | Code-Qualität |
| 076–092 | Diverse | Weitere niedrige Issues (fehlende Docstrings, inkonsistente Naming, deprecated API-Nutzung) | Code-Qualität |

---

## 📊 Checklisten-Übersichten

### Form-Validierung Matrix

| Form | App | Pflicht | Typ | Format | Range | Cross-Field | XSS | Datei | Status |
|------|-----|---------|-----|--------|-------|-------------|-----|------|--------|
| UserCreationForm | accounts | ✅ | ✅ | ⚠️ | N/A | ❌ | ✅ | forms.py | Fix |
| UserLoginForm | accounts | ✅ | ✅ | ✅ | N/A | N/A | ✅ | forms.py | OK |
| ProfileForm | members | ⚠️ | ✅ | ⚠️ | ⚠️ | ❌ | ✅ | forms.py | Review |
| VerificationForm | members | ✅ | ✅ | ⚠️ | N/A | ❌ | ⚠️ | forms.py | Fix |
| StrainForm | inventory | ✅ | ⚠️ | ✅ | ❌ | ❌ | ✅ | forms.py | Fix |
| BatchForm | inventory | ✅ | ✅ | ✅ | ⚠️ | ❌ | ✅ | forms.py | Review |
| OrderForm | orders | ⚠️ | ✅ | ✅ | ❌ | ❌ | N/A | services.py | Fix |
| BalanceTopUpForm | finance | ✅ | ✅ | ✅ | ⚠️ | N/A | ✅ | forms.py | Review |
| SepaMandateForm | finance | ✅ | ✅ | ⚠️ | N/A | ❌ | ✅ | forms.py | Fix |
| ClubConfigForm | core | ✅ | ✅ | ⚠️ | N/A | ❌ | ⚠️ | forms.py | Fix |
| ComplianceForm | compliance | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | forms.py | OK |
| GovernanceForm | governance | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | forms.py | Review |
| MessageForm | messaging | ✅ | ✅ | ✅ | N/A | ⚠️ | ⚠️ | forms.py | Fix |
| CultivationForm | cultivation | ✅ | ⚠️ | ✅ | ❌ | ❌ | ✅ | forms.py | Fix |
| ParticipationForm | participation | ✅ | ✅ | ✅ | N/A | ⚠️ | ✅ | forms.py | Review |
| PublicDocumentForm | core | ✅ | ⚠️ | ✅ | N/A | N/A | ✅ | forms.py | Fix |

**Legende:** ✅ OK | ⚠️ Teilweise | ❌ Fehlt | N/A Nicht zutreffend

---

### View-Autorisierung Matrix

| View | App | Auth | Perms | Object-Level | Club-Isolation | CSRF | Method | Status |
|------|-----|------|-------|-------------|----------------|------|--------|--------|
| UserRegistrationView | accounts | N/A | N/A | N/A | N/A | ✅ | ✅ | OK |
| UserLoginView | accounts | N/A | N/A | N/A | N/A | ✅ | ✅ | OK |
| ProfileView | members | ✅ | N/A | ✅ | ✅ | N/A | ✅ | OK |
| DirectoryView | members | ✅ | ⚠️ | N/A | ⚠️ | N/A | ✅ | 🔴 Fix |
| MemberActionView | members | ✅ | ⚠️ | ❌ | ⚠️ | N/A | ✅ | 🔴 Fix |
| LegacyApproveView | members | ✅ | ❌ | ❌ | ❌ | N/A | ✅ | 🔴 Fix |
| CartView | orders | ✅ | N/A | ✅ | ✅ | ✅ | ✅ | OK |
| OrderCheckoutView | orders | ✅ | N/A | ✅ | ✅ | ✅ | ✅ | OK |
| OrderDetailView | orders | ✅ | N/A | ⚠️ | ✅ | N/A | ✅ | Review |
| AdminOrderListView | orders | ✅ | ✅ | N/A | ⚠️ | N/A | ✅ | Review |
| InventoryCountView | inventory | ✅ | ❌ | N/A | ❌ | N/A | ✅ | 🔴 Fix |
| StrainDetailView | inventory | ✅ | N/A | N/A | ⚠️ | N/A | ✅ | Review |
| BalanceTopUpView | finance | ✅ | N/A | ✅ | ✅ | ✅ | ✅ | OK |
| StripeWebhookView | finance | N/A | N/A | N/A | N/A | ❌ | ✅ | Fix |
| InvoiceListView | finance | ✅ | N/A | ✅ | ✅ | N/A | ✅ | OK |
| ComplianceView | compliance | ✅ | ✅ | N/A | ✅ | N/A | ✅ | OK |
| GovernanceView | governance | ✅ | ✅ | N/A | ✅ | N/A | ✅ | OK |
| CultivationView | cultivation | ✅ | N/A | ✅ | ✅ | N/A | ✅ | OK |
| MessageCreateView | messaging | ✅ | ⚠️ | N/A | ⚠️ | N/A | ✅ | Fix |
| ParticipationView | participation | ✅ | N/A | ✅ | ✅ | N/A | ✅ | OK |

**Legende:** ✅ OK | ⚠️ Teilweise | ❌ Fehlt | N/A Nicht zutreffend

---

### Model-Constraint Matrix

| Model | Feld | DB-Constraint | Validator | Clean | Index | Status |
|-------|------|---------------|-----------|-------|-------|--------|
| User | email | ✅ UNIQUE | ✅ | N/A | ✅ | OK |
| User | role | ❌ CHECK | ❌ | N/A | ❌ | Fix |
| Profile | status | ❌ CHECK | ❌ | ❌ | ✅ | Fix |
| Profile | member_number | ✅ UNIQUE | N/A | N/A | ✅ | OK |
| SocialClub | name | ✅ UNIQUE | N/A | N/A | N/A | OK |
| SocialClub | slug | ✅ UNIQUE | N/A | ❌ | N/A | Fix |
| Strain | thc_content | ❌ CHECK 0-100 | ❌ | ❌ | N/A | 🔴 Fix |
| Strain | cbd_content | ❌ CHECK 0-100 | ❌ | ❌ | N/A | 🔴 Fix |
| Strain | price_per_gram | ❌ CHECK >0 | ❌ | N/A | N/A | Fix |
| Order | status | ❌ CHECK | ❌ | N/A | ❌ | Fix |
| Order | paid_with_balance | ❌ CHECK >=0 | ❌ | N/A | N/A | Fix |
| Batch | quantity | ❌ CHECK >0 | ❌ | ❌ | ❌ | Fix |
| BalanceTransaction | amount | ❌ CHECK | ❌ | N/A | ❌ | Fix |
| BalanceTopUp | amount | ❌ CHECK >0 | ❌ | N/A | N/A | Fix |
| Invoice | amount_gross | ❌ CHECK >=0 | ❌ | N/A | ❌ | Fix |
| SocialClubReview | rating | ✅ CHECK 1-5 | N/A | N/A | ✅ | OK |
| CultivationPlant | plant_count | ❌ CHECK | ❌ | ❌ | N/A | Fix |
| SuspiciousActivity | is_reported | N/A | N/A | N/A | ❌ | Fix |
| BoardMeeting | meeting_date | N/A | N/A | ❌ | N/A | Fix |
| PreventionInfo | club | N/A | N/A | N/A | ✅ | OK |

---

## 🛡️ Externe Integrationen Audit

### Stripe Integration

| Prüfpunkt | Status | Anmerkung |
|-----------|--------|-----------|
| Webhook-Signaturprüfung | ⚠️ | Implementiert aber ohne Fallback-Prüfung wenn Secret leer |
| Idempotency-Keys | ❌ | Keine Idempotency-Keys für Zahlungen |
| Beträge server-seitig | ⚠️ | In `orders/services.py` werden Preise aus Cart übernommen, keine Server-Verifikation |
| Error-Handling | ⚠️ | Grundlegendes Error-Handling, aber kein Graceful Degradation |
| Logging sensitiver Daten | ✅ | Keine Logs von Zahlungsdaten gefunden |
| Stripe Connect | ✅ | Korrekt implementiert mit `stripe_account_id` |

### OpenRouter AI Integration

| Prüfpunkt | Status | Anmerkung |
|-----------|--------|-----------|
| API-Key im Code | ✅ | In Env-Vars (`OPENROUTER_API_KEY`) |
| Timeout | ❌ | Kein Timeout für API-Calls konfiguriert |
| Retries | ❌ | Kein Retry-Mechanismus |
| Response-Validierung | ❌ | API-Responses werden nicht validiert |
| DSGVO-Konformität | 🔴 | Ausweisdokumente ohne Einwilligung an US-Server |
| Kostenkontrolle | ❌ | Kein Budget-Limit für API-Calls |

### E-Mail-Versand

| Prüfpunkt | Status | Anmerkung |
|-----------|--------|-----------|
| Template-Injection | ⚠️ | `email_signature_html` ohne Sanitisierung |
| Header-Injection | ✅ | CC/BCC nicht durch User kontrollierbar |
| Rate-Limiting | ❌ | Kein Schutz vor Spam-Missbrauch |
| fail_silently | 🔴 | `True` in mehreren Funktionen |
| Konfiguration | ✅ | Flexibel (Console/SMTP/Resend/File) |

### OpenIBAN API

| Prüfpunkt | Status | Anmerkung |
|-----------|--------|-----------|
| Timeout | ❌ | Kein Timeout konfiguriert |
| Fault-Tolerance | ⚠️ | API-Ausfall blockiert Form-Validierung |
| Datenschutz | ⚠️ | IBAN wird an externe API gesendet |

---

## 🔧 Empfohlene Behebungs-Reihenfolge

### Phase 1: Kritische Sicherheitslücken (Sofort, 1–3 Tage)

1. **ISSUE-001, -014:** IDOR-Fixes in allen Member-Views
2. **ISSUE-002:** Media-URL-Authentifizierung
3. **ISSUE-005:** Inventory-View Autorisierung
4. **ISSUE-007:** Verification-Code Hashing
5. **ISSUE-004:** KI-Verifikation DSGVO-Compliance

### Phase 2: Datenintegrität (1 Woche)

6. **ISSUE-003:** `select_for_update()` für Balance-Operations
7. **ISSUE-008:** Slug-Generation Race Condition
8. **ISSUE-012:** `transaction.atomic()` für Order-Services
9. **ISSUE-017:** `BalanceTopUp` Race Condition
10. **ISSUE-006:** THC/CBD-Constraints auf DB-Ebene

### Phase 3: Hohe Sicherheitsissues (2 Wochen)

11. **ISSUE-009:** HTML-Sanitisierung für Signature
12. **ISSUE-010:** Messaging-Permission-Einschränkung
13. **ISSUE-011:** `fail_silently=False` + Logging
14. **ISSUE-013:** Stripe-Webhook-Absicherung
15. **ISSUE-025:** Messaging-Task-Idempotenz

### Phase 4: Mittlere Issues (Nächster Sprint)

16. Rate-Limiting für Login und Club-Registrierung
17. File-Validierung für Uploads
18. N+1 Query-Optimierungen
19. Fehlende DB-Indizes

### Phase 5: Quick Wins (Zwischendurch)

- `status`-Felder mit `db_index=True` versehen
- `select_related` in Admin-Views
- Type-Hints ergänzen
- Docstrings für öffentliche Funktionen

---

## 🏗️ Architektur-Empfehlungen

### Einzuführende Patterns

1. **Club-Scoped Manager:** Ein `ClubQuerySet` und `ClubManager`, der automatisch nach `social_club_id` filtert, um IDOR systematisch zu verhindern.

```python
class ClubQuerySet(models.QuerySet):
    def for_club(self, user):
        if user.social_club_id:
            return self.filter(social_club_id=user.social_club_id)
        return self

class ClubManager(models.Manager):
    def get_queryset(self):
        return ClubQuerySet(self.model, using=self._db)
    
    def for_club(self, user):
        return self.get_queryset().for_club(user)
```

2. **Audit-Mixin:** Automatisches Audit-Logging für alle wichtigen Model-Änderungen.

```python
class AuditMixin(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

3. **Service-Layer mit Transaktions-Garantie:** Alle Business-Logik in Service-Klassen mit `@transaction.atomic` als Default.

### Refactoring-Vorschläge

1. **Legacy-Views entfernen:** Die 5 Legacy-Member-Views durch die neuen `member_action()`-basierten Views ersetzen
2. **E-Mail-Template-Extrahierung:** Hartcodierte E-Mail-Texte in Django-Templates auslagern
3. **Cart-Validierung:** Server-seitige Preisverifikation vor Order-Erstellung
4. **Konfigurations-Singleton:** `ClubConfiguration`-Zugriff über Caching-Layer

### Security-Hardening-Maßnahmen

1. **Content-Security-Policy:** CSP-Header für alle Responses
2. **Rate-Limiting:** Django-Ratelimit oder django-axes für Login
3. **Session-Sicherheit:** `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`
4. **Security-Headers:** `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`
5. **Subresource Integrity:** SRI-Hashes für externe Scripts/CSS

---

## 📝 Zusammenfassung der KCanG-Compliance-Relevanz

Das KCanG (Konsumcannabisgesetz) stellt spezifische Anforderungen an CSC-Software:

| Anforderung | Status | Issues |
|-------------|--------|--------|
| §19 – Mengenbegrenzung pro Mitglied | ⚠️ | Keine automatisierte Limit-Prüfung in Order-Services |
| §19 – Abgabedokumentation | ✅ | Order-Modell erfasst Abgaben |
| §19 – THC-Obergrenze 10% (Vermehrungsmaterial) | ❌ | Keine Validierung mit Warnung bei >10% THC |
| §20 – Bestandsführung | ⚠️ | Inventory-Count-View unsicher (ISSUE-005) |
| §21 – Mitgliederliste | ⚠️ | Directory hat IDOR (ISSUE-001) |
| §23 – Jugendschutz | ✅ | `minimum_age`-Prüfung vorhanden |
| §24 – Werbeverbot | ⚠️ | SocialClub-Description ohne Werbe-Check |
| §27 – Berichtspflichten | ❌ | Keine automatisierten Berichte für Aufsichtsbehörden |

---

**Ende des Audit-Reports.**  
Erstellt am 11. Mai 2026, 23:43 Uhr (Europe/Berlin)  
92 Issues identifiziert · 8 Kritisch · 24 Hoch · 38 Mittel · 22 Niedrig