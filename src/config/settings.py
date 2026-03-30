from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value != "":
            return value
    return default


def _env_bool(*names: str, default: bool = False) -> bool:
    raw = _env_first(*names)
    if raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_csv(*names: str) -> list[str]:
    raw = _env_first(*names)
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]

# SECURITY WARNING: keep the secret key used in production secret!
# In production, DJANGO_SECRET_KEY must be set and DJANGO_DEBUG must be "0"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if _env_bool("DJANGO_DEBUG", default=True):
        # Only use fallback in development
        SECRET_KEY = "dev-secret-key-not-for-production"
    else:
        raise ValueError("DJANGO_SECRET_KEY environment variable must be set in production!")

DEBUG = _env_bool("DJANGO_DEBUG", default=True)

# SECURITY WARNING: don't run with debug turned on in production!
if DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
else:
    allowed_hosts = _env_csv("ALLOWED_HOSTS", "DJANGO_ALLOWED_HOSTS")
    if allowed_hosts:
        ALLOWED_HOSTS = allowed_hosts
    else:
        raise ValueError("ALLOWED_HOSTS or DJANGO_ALLOWED_HOSTS environment variable must be set in production!")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts",
    "apps.core",
    "apps.members",
    "apps.inventory",
    "apps.orders",
    "apps.compliance",
    "apps.finance",
    "apps.participation",
    "apps.cultivation",
    "apps.messaging",
    "apps.governance",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.ga_tracking_id",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DATABASE_NAME", "csc"),
        "USER": os.getenv("DATABASE_USER", "csc"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "csc"),
        "HOST": os.getenv("DATABASE_HOST", "localhost"),
        "PORT": os.getenv("DATABASE_PORT", "5432"),
    }
}

RUNNING_PYTEST = any("pytest" in arg for arg in sys.argv)

if (
    os.getenv("USE_SQLITE", "0") == "1"
    or os.getenv("USE_SQLITE_FOR_TESTS", "0") == "1"
    or RUNNING_PYTEST
):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(os.getenv("DJANGO_STATIC_ROOT", "/tmp/csc-staticfiles"))
EXPORT_ROOT = Path(os.getenv("CSC_EXPORT_ROOT", "/tmp/csc-exports"))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if RUNNING_PYTEST
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Google Analytics
GA_TRACKING_ID = os.getenv("GA_TRACKING_ID", "")

# Test User fuer Dev-Login / GUI-Tests
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "")
DEV_LOGIN_ALLOWED_DOMAIN = os.getenv("DEV_LOGIN_ALLOWED_DOMAIN", "@test.local")

# Site-URL fuer absolute Links (z.B. Tracking-Pixel in E-Mails)
SITE_URL = _env_first("SITE_URL", "APP_PUBLIC_URL", default="http://localhost:8000")
CSRF_TRUSTED_ORIGINS = _env_csv("CSRF_TRUSTED_ORIGINS", "DJANGO_CSRF_TRUSTED_ORIGINS")
if SITE_URL.startswith(("http://", "https://")):
    site_origin = SITE_URL.rstrip("/")
    if site_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(site_origin)

# E-Mail-Versand
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@localhost")
EMAIL_DELIVERY_MODE = os.getenv("EMAIL_DELIVERY_MODE", "console")  # console | smtp | resend
USE_RESEND = os.getenv("USE_RESEND", "0") == "1"

if EMAIL_DELIVERY_MODE == "smtp" or USE_RESEND:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "1") == "1"
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Vereins-Konfiguration
MEMBER_CAPACITY = int(os.getenv("MEMBER_CAPACITY", "500"))  # Maximale Mitgliederzahl
LOW_STOCK_THRESHOLD_EUR = os.getenv("LOW_STOCK_THRESHOLD_EUR", "25.00")  # Mindestbestand in EUR
