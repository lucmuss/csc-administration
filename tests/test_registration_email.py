from django.urls import reverse
from django.test import override_settings


import pytest

from apps.core.models import SocialClub


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_registration_sends_confirmation_email(client, mailoutbox, member_user):
    club = SocialClub.objects.create(
        name="Mail Test Club",
        email="mail-club@example.com",
        street_address="Testweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+4915111111111",
        is_active=True,
        is_approved=True,
    )
    response = client.post(
        reverse("members:register"),
        data={
            "first_name": "Erika",
            "last_name": "Muster",
            "email": "erika@example.com",
            "social_club": str(club.id),
            "birth_date": "1990-01-01",
            "password": "StrongPass123!",
            "accept_terms": "on",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["erika@example.com"]
    assert "Registrierung eingegangen" in mailoutbox[0].subject
