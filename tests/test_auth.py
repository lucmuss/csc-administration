import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse

from apps.accounts.forms import EmailAuthenticationForm, StyledPasswordResetForm


@pytest.mark.django_db
def test_login_success(client, member_user):
    response = client.post(
        reverse("accounts:login"),
        data={"username": member_user.email, "password": "StrongPass123!"},
    )
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
    assert reverse("accounts:password_reset") in response.content.decode("utf-8")


def test_impressum_alias_redirects_to_imprint(client):
    response = client.get("/impressum/")

    assert response.status_code == 302
    assert response["Location"].endswith("/imprint/")
