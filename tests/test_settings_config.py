import importlib

from config import settings as app_settings


def reload_settings():
    return importlib.reload(app_settings)


def test_env_bool_accepts_true_string(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "true")
    assert app_settings._env_bool("DJANGO_DEBUG", default=False) is True


def test_production_env_uses_django_prefixed_host_and_csrf_settings(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "csc.kolibri-kollektiv.eu,web")
    monkeypatch.delenv("CSRF_TRUSTED_ORIGINS", raising=False)
    monkeypatch.setenv("DJANGO_CSRF_TRUSTED_ORIGINS", "https://csc.kolibri-kollektiv.eu")
    monkeypatch.delenv("SITE_URL", raising=False)
    monkeypatch.setenv("APP_PUBLIC_URL", "https://csc.kolibri-kollektiv.eu")

    settings = reload_settings()

    assert settings.DEBUG is False
    assert settings.ALLOWED_HOSTS == ["csc.kolibri-kollektiv.eu", "web"]
    assert "https://csc.kolibri-kollektiv.eu" in settings.CSRF_TRUSTED_ORIGINS
    assert settings.SITE_URL == "https://csc.kolibri-kollektiv.eu"


def test_site_url_is_added_to_csrf_trusted_origins(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALLOWED_HOSTS", "csc.kolibri-kollektiv.eu")
    monkeypatch.setenv("SITE_URL", "https://csc.kolibri-kollektiv.eu")
    monkeypatch.delenv("CSRF_TRUSTED_ORIGINS", raising=False)
    monkeypatch.delenv("DJANGO_CSRF_TRUSTED_ORIGINS", raising=False)

    settings = reload_settings()

    assert settings.CSRF_TRUSTED_ORIGINS == ["https://csc.kolibri-kollektiv.eu"]


def test_branding_and_health_defaults_can_be_configured(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALLOWED_HOSTS", "club.example")
    monkeypatch.setenv("APP_NAME", "Club Suite")
    monkeypatch.setenv("APP_TAGLINE", "Mitglieder und Betrieb")
    monkeypatch.setenv("HEALTH_ALLOWED_IPS", "10.0.0.1,127.0.0.1")

    settings = reload_settings()

    assert settings.APP_NAME == "Club Suite"
    assert settings.APP_TAGLINE == "Mitglieder und Betrieb"
    assert settings.HEALTH_ALLOWED_IPS == ["10.0.0.1", "127.0.0.1"]


def test_email_delivery_mode_file_uses_file_backend(monkeypatch, tmp_path):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALLOWED_HOSTS", "club.example")
    monkeypatch.setenv("EMAIL_DELIVERY_MODE", "file")
    monkeypatch.setenv("EMAIL_FILE_PATH", str(tmp_path / "mail-out"))

    settings = reload_settings()

    assert settings.EMAIL_BACKEND == "django.core.mail.backends.filebased.EmailBackend"
    assert str(settings.EMAIL_FILE_PATH).endswith("mail-out")


def test_app_version_can_be_set_via_env(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALLOWED_HOSTS", "club.example")
    monkeypatch.setenv("APP_VERSION", "0.1")

    settings = reload_settings()

    assert settings.APP_VERSION == "0.1"


def test_app_version_defaults_to_pyproject_version(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALLOWED_HOSTS", "club.example")
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.delenv("RELEASE_VERSION", raising=False)

    settings = reload_settings()

    assert settings.APP_VERSION
    assert settings.APP_VERSION != "dev"
