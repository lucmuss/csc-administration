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
