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
    "apps.members.middleware.MemberOnboardingMiddleware",
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
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
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
DEFAULT_FROM_EMAIL = _env_first("DEFAULT_FROM_EMAIL", "DJANGO_DEFAULT_FROM_EMAIL", default="noreply@localhost")
EMAIL_DELIVERY_MODE = _env_first("EMAIL_DELIVERY_MODE", default="console")  # console | smtp | resend
USE_RESEND = _env_bool("USE_RESEND", default=False)

if EMAIL_DELIVERY_MODE == "smtp" or USE_RESEND:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = _env_first("EMAIL_HOST", "DJANGO_EMAIL_HOST", default="")
    EMAIL_PORT = int(_env_first("EMAIL_PORT", "DJANGO_EMAIL_PORT", default="587"))
    EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", "DJANGO_EMAIL_USE_TLS", default=True)
    EMAIL_USE_SSL = _env_bool("EMAIL_USE_SSL", "DJANGO_EMAIL_USE_SSL", default=False)
    if EMAIL_USE_SSL:
        EMAIL_USE_TLS = False
    EMAIL_HOST_USER = _env_first("EMAIL_HOST_USER", "DJANGO_EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = _env_first("EMAIL_HOST_PASSWORD", "DJANGO_EMAIL_HOST_PASSWORD", default="")
    EMAIL_TIMEOUT = int(_env_first("EMAIL_TIMEOUT", "DJANGO_EMAIL_TIMEOUT", default="10"))
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Vereins-Konfiguration
MEMBER_CAPACITY = int(os.getenv("MEMBER_CAPACITY", "500"))  # Maximale Mitgliederzahl
LOW_STOCK_THRESHOLD_EUR = os.getenv("LOW_STOCK_THRESHOLD_EUR", "25.00")  # Mindestbestand in EUR
MEMBER_MINIMUM_AGE = int(_env_first("MEMBER_MINIMUM_AGE", "DJANGO_MEMBER_MINIMUM_AGE", default="21"))
MEMBER_MONTHLY_FEE = _env_first("MEMBER_MONTHLY_FEE", default="24.00")
STRIPE_SECRET_KEY = _env_first("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = _env_first("STRIPE_PUBLISHABLE_KEY", default="")
ORDER_SELF_CANCEL_HOURS = int(_env_first("ORDER_SELF_CANCEL_HOURS", default="24"))
CLUB_NAME = _env_first("CLUB_NAME", default="Cannabis Social Club Leipzig Sued e.V.")
CLUB_BOARD_REPRESENTATIVES = _env_first("CLUB_BOARD_REPRESENTATIVES", default="")
CLUB_REGISTER_ENTRY = _env_first("CLUB_REGISTER_ENTRY", default="")
CLUB_VAT_ID = _env_first("CLUB_VAT_ID", default="")
CLUB_SUPERVISORY_AUTHORITY = _env_first("CLUB_SUPERVISORY_AUTHORITY", default="")
CLUB_CONTENT_RESPONSIBLE = _env_first("CLUB_CONTENT_RESPONSIBLE", default="")
GENERAL_MEETING_INVITATION_LEAD_DAYS = int(
    _env_first("GENERAL_MEETING_INVITATION_LEAD_DAYS", default="14")
)
GENERAL_MEETING_REMINDER_LEAD_HOURS = int(
    _env_first("GENERAL_MEETING_REMINDER_LEAD_HOURS", default="24")
)
GENERAL_MEETING_AGENDA_SUBMISSION_EMAIL = _env_first(
    "GENERAL_MEETING_AGENDA_SUBMISSION_EMAIL",
    default=DEFAULT_FROM_EMAIL,
)
CLUB_CONTACT_EMAIL = _env_first("CLUB_CONTACT_EMAIL", default=DEFAULT_FROM_EMAIL)
CLUB_CONTACT_PHONE = _env_first("CLUB_CONTACT_PHONE", default="")
CLUB_CONTACT_ADDRESS = _env_first("CLUB_CONTACT_ADDRESS", default="")
