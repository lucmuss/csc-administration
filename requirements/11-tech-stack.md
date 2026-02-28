# Tech Stack - CSC-Admin

**Basierend auf:** RedFlag Analyzer Tech Stack  
**Prinzipien:** UV-Only, PostgreSQL-Only, Open Source

---

## Core Stack

### Backend Framework
- • **Django 5.0.1** - Hauptframework
- • **Python 3.11+** - Programmiersprache
- • **django-environ 0.11.2** - Umgebungsvariablen

### Database
- • **PostgreSQL 16** - Primäre Datenbank (PostgreSQL-Only Rule!)
- • **psycopg2-binary 2.9.9** - PostgreSQL Adapter
- • **dj-database-url 2.1.0** - Datenbank-URL Parsing
- • ❌ **Kein Redis** (außer explizit gefordert)
- • ❌ **Kein Celery** (außer explizit gefordert)

### Package Manager
- • **UV** - Einziger erlaubter Package Manager (UV-Only Rule!)
- • ❌ **Kein pip** direkt
- • ❌ **Kein requirements.txt**

---

## Frontend

### CSS Framework
- • **django-tailwind 3.8.0** - Utility-First CSS
- • Alternative: Bootstrap 5 (wenn Tailwind zu komplex)

### HTMX Integration
- • **django-htmx 1.17.3** - Dynamische Updates ohne SPA
- • Server-Side Rendering mit reaktiven Elementen

### PWA Support
- • **django-pwa 1.1.0** - Progressive Web App (optional)
- • Offline-Fähigkeit für Mitglieder

---

## Authentication & Security

### User Auth
- • **django-allauth 0.61.1** - Authentifizierung
- • E-Mail basierter Login
- • Social Auth (optional später)

### Password Hashing
- • **argon2-cffi 23.1.0** - Sicheres Passwort-Hashing

### Security
- • **django-ratelimit 4.1.0** - Rate Limiting
- • **django-csp** - Content Security Policy (empfohlen)
- • **django-cors-headers** - CORS (falls API)

---

## Email & Communication

### Email Service
- • **resend 0.7.0** - Transaktions-E-Mails
- • Alternative: django.core.mail mit SMTP

### Newsletter
- • **django-newsletter** oder eigene Implementation
- • HTML + Plain Text E-Mails

---

## File Handling

### Images
- • **Pillow 10.2.0** - Bildverarbeitung
- • Mitgliedsfotos, Ausweisbilder

### Documents
- • **weasyprint 60.1** - PDF Generierung (optional)
- • Für Quittungen, Berichte

---

## Development Tools

### Linting & Formatting
- • **ruff 0.1.0+** - Linter und Formatter
- • **mypy 1.0+** - Type Checking
- • **pre-commit 3.0+** - Git Hooks

### Testing
- • **pytest 7.0+** - Test Framework
- • **pytest-django 4.0+** - Django Integration
- • **pytest-cov 4.0+** - Coverage
- • **playwright 1.50.0+** - E2E Tests

---

## Production

### Server
- • **gunicorn 21.2.0** - WSGI Server
- • **whitenoise 6.6.0** - Static Files

### Monitoring
- • **sentry-sdk 2.50.0** - Error Tracking (optional)

---

## Project Structure

```
csc-admin/
├── src/
│   ├── csc_admin_project/     # Django settings
│   ├── apps/
│   │   ├── core/              # Base models
│   │   ├── members/           # Mitgliederverwaltung
│   │   ├── inventory/         # Bestand/Anbau
│   │   ├── dispensing/        # Ausschank
│   │   ├── compliance/        # Berichte
│   │   ├── accounting/        # Finanzen
│   │   └── newsletter/        # Kommunikation
│   ├── templates/             # HTML Templates
│   ├── static/                # CSS, JS, Images
│   └── manage.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── requirements/              # Dokumentation
├── docs/
├── Justfile                   # Commands
├── pyproject.toml             # UV Dependencies
├── docker-compose.yml         # PostgreSQL only
└── README.md
```

---

## pyproject.toml Template

```toml
[project]
name = "csc-admin"
version = "0.1.0"
description = "Cannabis Social Club Administration Software"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    # Django Core
    "Django==5.0.1",
    "django-environ==0.11.2",
    
    # Database (PostgreSQL ONLY)
    "psycopg2-binary==2.9.9",
    "dj-database-url==2.1.0",
    
    # Auth & Security
    "django-allauth==0.61.1",
    "argon2-cffi==23.1.0",
    "django-ratelimit==4.1.0",
    
    # Frontend
    "django-htmx==1.17.3",
    "django-tailwind==3.8.0",
    
    # Email
    "resend==0.7.0",
    
    # Utilities
    "python-dotenv==1.0.1",
    "Pillow==10.2.0",
    "markdown==3.5.1",
    
    # Production
    "gunicorn==21.2.0",
    "whitenoise==6.6.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",
    "mypy>=1.0",
    "pre-commit>=3.0",
    "pytest>=7.0",
    "pytest-django>=4.0",
    "pytest-cov>=4.0",
    "playwright>=1.50.0",
]

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
include-package-data = true

[tool.setuptools.package-dir]
"" = "src"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = false
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["src"]
DJANGO_SETTINGS_MODULE = "csc_admin_project.settings_test"
addopts = [
    "--verbose",
    "--strict-markers",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
]
```

---

## Justfile Commands (from RedFlag)

```just
setup:
    uv venv
    uv sync --extra dev
    cp -n .env.example .env || true

migrate:
    uv run python src/manage.py migrate

dev:
    uv run python src/manage.py runserver 0.0.0.0:8000

format:
    uv run ruff format src tests

lint:
    uv run ruff check src tests

typecheck:
    uv run mypy src

test:
    PYTHONPATH=src uv run pytest

ci: lint typecheck test
```

---

## Docker (PostgreSQL Only)

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: csc_admin
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgres://postgres:postgres@db:5432/csc_admin
    depends_on:
      - db
    # KEIN Redis!

volumes:
  postgres_data:
```

---

## Unterschiede zu RedFlag Analyzer

| Feature | RedFlag | CSC-Admin |
|---------|---------|-----------|
| Payments | Stripe (kommerziell) | ❌ Keine Zahlungen (Spenden) |
| PDF Export | WeasyPrint (optional) | ❌ Optional |
| i18n | django-modeltranslation | ❌ Nur Deutsch (erstmal) |
| PWA | Ja | Optional |
| Newsletter | ❌ | ✅ Ja |
| Member Assembly | ❌ | ✅ Ja |

---

**Quelle:** Tech Stack basiert auf RedFlag Analyzer  
**Angepasst:** Für CSC-Bedürfnisse (non-profit, compliance)

---

**Nächste Schritte:**
1. [ ] pyproject.toml erstellen
2. [ ] Django Projekt-Struktur aufsetzen
3. [ ] Docker-Compose erstellen
4. [ ] Justfile erstellen
5. [ ] Erste Models implementieren