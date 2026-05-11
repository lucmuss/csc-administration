from __future__ import annotations

import pytest
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

from apps.accounts.models import User
from apps.accounts.validators import (
    GermanCommonPasswordValidator,
    GermanMinimumLengthValidator,
    GermanNumericPasswordValidator,
    GermanUserAttributeSimilarityValidator,
)
from apps.accounts.views import MemberPasswordChangeView
from apps.core.models import SocialClub


pytestmark = pytest.mark.django_db


def _create_active_club(name: str, email: str) -> SocialClub:
    return SocialClub.objects.create(
        name=name,
        email=email,
        street_address="Testweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49123456789",
        is_active=True,
        is_approved=True,
    )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_password_reset_view_renders_and_redirects_even_for_unknown_email(client):
    response_get = client.get(reverse("accounts:password_reset"))
    assert response_get.status_code == 200

    response_post = client.post(reverse("accounts:password_reset"), data={"email": "unbekannt@example.com"})
    assert response_post.status_code == 302
    assert response_post.url == reverse("accounts:password_reset_done")
    assert len(mail.outbox) == 0


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_password_reset_full_confirm_flow(client, member_user):
    response_done = client.get(reverse("accounts:password_reset_done"))
    assert response_done.status_code == 200

    uid = urlsafe_base64_encode(force_bytes(member_user.pk))
    token = default_token_generator.make_token(member_user)
    confirm_url = reverse("accounts:password_reset_confirm", args=[uid, token])

    response_confirm_get = client.get(confirm_url, follow=True)
    assert response_confirm_get.status_code == 200

    set_password_url = response_confirm_get.request["PATH_INFO"]
    response_confirm_post = client.post(
        set_password_url,
        data={
            "new_password1": "BrandNeuPasswort123!",
            "new_password2": "BrandNeuPasswort123!",
        },
    )
    assert response_confirm_post.status_code == 302
    assert response_confirm_post.url == reverse("accounts:password_reset_complete")

    response_complete = client.get(reverse("accounts:password_reset_complete"))
    assert response_complete.status_code == 200

    login_response = client.post(
        reverse("accounts:login"),
        data={"username": member_user.email, "password": "BrandNeuPasswort123!"},
    )
    assert login_response.status_code == 302
    assert login_response.url == reverse("core:dashboard")


def test_password_change_view_sets_autocomplete_attributes(member_user):
    rf = RequestFactory()
    request = rf.get(reverse("accounts:password_change"))
    request.user = member_user

    view = MemberPasswordChangeView()
    view.setup(request)
    form = view.get_form()

    assert form.fields["old_password"].widget.attrs["autocomplete"] == "current-password"
    assert form.fields["new_password1"].widget.attrs["autocomplete"] == "new-password"
    assert form.fields["new_password2"].widget.attrs["autocomplete"] == "new-password"
    assert "form-input" in form.fields["old_password"].widget.attrs["class"]


@override_settings(DEBUG=False)
def test_dev_login_redirects_when_debug_is_false(client):
    response = client.get(reverse("accounts:dev_login"), REMOTE_ADDR="127.0.0.1")
    assert response.status_code == 302
    assert response.url == reverse("accounts:login")


@override_settings(DEBUG=True)
def test_dev_login_forbids_non_localhost(client):
    response = client.get(reverse("accounts:dev_login"), REMOTE_ADDR="203.0.113.10")
    assert response.status_code == 403
    assert "localhost" in response.content.decode("utf-8")


@override_settings(DEBUG=True, TEST_USER_EMAIL="dev@test.local", DEV_LOGIN_ALLOWED_DOMAIN="@test.local")
def test_dev_login_creates_board_user_on_localhost(client):
    assert not User.objects.filter(email="dev@test.local").exists()

    response = client.get(reverse("accounts:dev_login"), REMOTE_ADDR="127.0.0.1")

    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")
    created = User.objects.get(email="dev@test.local")
    assert created.role == User.ROLE_BOARD
    assert created.is_staff is True
    assert created.is_superuser is True
    assert client.session.get("_auth_user_id") == str(created.pk)


@override_settings(DEBUG=True, TEST_USER_EMAIL="existing@test.local", DEV_LOGIN_ALLOWED_DOMAIN="@test.local")
def test_dev_login_uses_existing_user_without_duplicate_creation(client):
    existing = User.objects.create_user(
        email="existing@test.local",
        password="StrongPass123!",
        first_name="Existing",
        last_name="User",
        role=User.ROLE_STAFF,
        is_staff=True,
    )
    before_count = User.objects.count()

    response = client.get(reverse("accounts:dev_login"), REMOTE_ADDR="127.0.0.1")

    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")
    assert User.objects.count() == before_count
    assert client.session.get("_auth_user_id") == str(existing.pk)


@override_settings(DEBUG=True, TEST_USER_EMAIL="dev@example.com", DEV_LOGIN_ALLOWED_DOMAIN="@test.local")
def test_dev_login_rejects_email_outside_allowed_domain(client):
    response = client.get(reverse("accounts:dev_login"), REMOTE_ADDR="127.0.0.1")
    assert response.status_code == 403
    assert "Domain" in response.content.decode("utf-8")


def test_legacy_register_downgrades_bootstrap_board_to_member(client):
    club = _create_active_club("Legacy Register Club", "legacy-register@example.com")
    assert User.objects.count() == 0

    response = client.post(
        reverse("accounts:register"),
        data={
            "first_name": "Lena",
            "last_name": "Neu",
            "email": "lena.neu@example.com",
            "social_club": str(club.id),
            "birth_date": "1990-01-01",
            "password1": "SicherPasswort123!",
            "password2": "SicherPasswort123!",
            "accept_terms": "on",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("accounts:login")
    created = User.objects.get(email="lena.neu@example.com")
    assert created.role == User.ROLE_MEMBER
    assert created.is_staff is False
    assert created.is_superuser is False


def test_german_user_attribute_similarity_validator_messages(member_user):
    validator = GermanUserAttributeSimilarityValidator()
    with pytest.raises(ValidationError) as exc_info:
        validator.validate("member@example.com", user=member_user)
    assert "zu aehnlich" in str(exc_info.value)
    assert "persoenlichen Angaben" in validator.get_help_text()


def test_german_user_attribute_similarity_validator_accepts_unrelated_password(member_user):
    validator = GermanUserAttributeSimilarityValidator()
    validator.validate("KomplettAnders123!", user=member_user)


def test_german_minimum_length_validator_and_help_text():
    validator = GermanMinimumLengthValidator(min_length=12)
    with pytest.raises(ValidationError) as exc_info:
        validator.validate("Kurz123!")
    assert "mindestens 12 Zeichen" in str(exc_info.value)
    assert "mindestens 12 Zeichen" in validator.get_help_text()
    validator.validate("LangGenug123!")


def test_german_common_password_validator_and_help_text():
    validator = GermanCommonPasswordValidator()
    with pytest.raises(ValidationError) as exc_info:
        validator.validate("password")
    assert "zu haeufig" in str(exc_info.value)
    assert "nicht zu haeufig" in validator.get_help_text()
    validator.validate("SeltenesPasswort123!")


def test_german_numeric_password_validator_and_help_text():
    validator = GermanNumericPasswordValidator()
    with pytest.raises(ValidationError) as exc_info:
        validator.validate("1234567890")
    assert "nur aus Zahlen" in str(exc_info.value)
    assert "nur aus Zahlen" in validator.get_help_text()
    validator.validate("12345Abc")
