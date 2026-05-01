import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse

from apps.accounts.forms import EmailAuthenticationForm, StyledPasswordResetForm
from apps.core.club import ACTIVE_FEDERAL_STATE_SESSION_KEY
from apps.core.models import SocialClub


@pytest.mark.django_db
def test_login_success(client, member_user):
    response = client.post(
        reverse("accounts:login"),
        data={"username": member_user.email, "password": "StrongPass123!"},
    )
    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")


@pytest.mark.django_db
def test_member_login_ignores_admin_next_redirect(client, member_user):
    response = client.post(
        reverse("accounts:login") + "?next=/orders/admin/",
        data={"username": member_user.email, "password": "StrongPass123!"},
    )

    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")


@pytest.mark.django_db
def test_authenticated_member_getting_orders_admin_is_redirected_to_dashboard(client, member_user):
    client.force_login(member_user)

    response = client.get(reverse("orders:admin_list"))

    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")


@pytest.mark.django_db
def test_member_profile_shows_visible_logout_action(client, member_user):
    client.force_login(member_user)

    response = client.get(reverse("members:profile"))

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert reverse("accounts:logout") in html
    assert "Abmelden" in html


def test_login_form_fields_use_styled_inputs():
    form = EmailAuthenticationForm()

    assert "form-input" in form.fields["username"].widget.attrs["class"]
    assert form.fields["username"].widget.attrs["autocomplete"] == "email"
    assert "form-input" in form.fields["password"].widget.attrs["class"]
    assert form.fields["password"].widget.attrs["autocomplete"] == "current-password"


def test_password_reset_form_uses_styled_email_input():
    form = StyledPasswordResetForm()

    assert "form-input" in form.fields["email"].widget.attrs["class"]
    assert form.fields["email"].widget.attrs["autocomplete"] == "email"


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_password_reset_request_sends_reset_email(client, member_user):
    response = client.post(reverse("accounts:password_reset"), data={"email": member_user.email})

    assert response.status_code == 302
    assert response.url == reverse("accounts:password_reset_done")
    assert len(mail.outbox) == 1
    assert member_user.email in mail.outbox[0].to


def test_login_template_links_to_password_reset(client):
    response = client.get(reverse("accounts:login"))

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert reverse("accounts:password_reset") in html
    assert reverse("core:privacy") in html
    assert reverse("core:documents") in html
    assert reverse("core:imprint") in html
    assert reverse("core:health") not in html


@pytest.mark.django_db
def test_login_form_keeps_state_selector_visible_when_only_state_is_saved(rf):
    SocialClub.objects.create(
        name="CSC Sachsen",
        email="sachsen@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49111",
        federal_state=SocialClub.BUNDESLAND_SN,
        is_approved=True,
        is_active=True,
    )
    request = rf.get(reverse("accounts:login"))
    request.session = {ACTIVE_FEDERAL_STATE_SESSION_KEY: SocialClub.BUNDESLAND_BW}

    form = EmailAuthenticationForm(request=request)

    assert "federal_state" in form.fields
    assert "social_club" in form.fields
    assert form.fields["social_club"].queryset.filter(name="CSC Sachsen").exists()


@pytest.mark.django_db
@override_settings(LOGIN_RATE_LIMIT_ATTEMPTS=2, LOGIN_RATE_LIMIT_WINDOW_SECONDS=60)
def test_login_rate_limit_blocks_repeated_failed_attempts(client, member_user):
    login_url = reverse("accounts:login")

    first = client.post(login_url, data={"username": member_user.email, "password": "wrong-password"})
    second = client.post(login_url, data={"username": member_user.email, "password": "wrong-password"})
    blocked = client.post(login_url, data={"username": member_user.email, "password": "wrong-password"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert blocked.status_code == 200
    assert "Zu viele fehlgeschlagene Anmeldeversuche" in blocked.content.decode("utf-8")


def test_impressum_alias_redirects_to_imprint(client):
    response = client.get("/impressum/")

    assert response.status_code == 302
    assert response["Location"].endswith("/imprint/")
