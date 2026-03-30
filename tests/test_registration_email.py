from django.urls import reverse
from django.test import override_settings


import pytest


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_registration_sends_confirmation_email(client, mailoutbox):
    response = client.post(
        reverse("members:register"),
        data={
            "first_name": "Erika",
            "last_name": "Muster",
            "email": "erika@example.com",
            "birth_date": "1990-01-01",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("accounts:login")
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["erika@example.com"]
    assert "Registrierung eingegangen" in mailoutbox[0].subject
