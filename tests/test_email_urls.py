import pytest
from django.test import RequestFactory, override_settings


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SITE_URL="https://csc.kolibri-kollektiv.eu",
    DEFAULT_FROM_EMAIL="info@kolibri-kollektiv.eu",
)
def test_registration_email_uses_site_url_for_login_link(mailoutbox):
    from apps.accounts.emails import send_registration_received_email
    from apps.accounts.models import User

    user = User.objects.create_user(
        email="erika@example.com",
        password="StrongPass123!",
        first_name="Erika",
        last_name="Muster",
    )
    request = RequestFactory().get("/", HTTP_HOST="csc.kolibri-kollektiv.eu", secure=True)

    assert send_registration_received_email(user, request) is True

    body = mailoutbox[0].body
    html = mailoutbox[0].alternatives[0][0]
    assert "https://csc.kolibri-kollektiv.eu/accounts/login/" in body
    assert "https://csc.kolibri-kollektiv.eu/accounts/login/" in html
    assert mailoutbox[0].from_email == "info@kolibri-kollektiv.eu"


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SITE_URL="https://csc.kolibri-kollektiv.eu",
    DEFAULT_FROM_EMAIL="info@kolibri-kollektiv.eu",
)
def test_login_alert_email_uses_site_url_for_buttons(mailoutbox):
    from apps.accounts.emails import send_login_alert_email
    from apps.accounts.models import User

    user = User.objects.create_user(
        email="nora@example.com",
        password="StrongPass123!",
        first_name="Nora",
        last_name="Kilic",
    )
    request = RequestFactory().get(
        "/accounts/login/",
        HTTP_HOST="csc.kolibri-kollektiv.eu",
        secure=True,
        HTTP_USER_AGENT="pytest",
        REMOTE_ADDR="127.0.0.1",
    )

    assert send_login_alert_email(user, request) is True

    body = mailoutbox[0].body
    html = mailoutbox[0].alternatives[0][0]
    assert "https://csc.kolibri-kollektiv.eu/" in body
    assert "https://csc.kolibri-kollektiv.eu/admin/password_change/" in body
    assert 'href="https://csc.kolibri-kollektiv.eu/' in html
    assert 'href="https://csc.kolibri-kollektiv.eu/admin/password_change/"' in html
    assert mailoutbox[0].from_email == "info@kolibri-kollektiv.eu"
