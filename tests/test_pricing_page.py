from datetime import date

import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.core.models import SocialClub
from apps.members.models import Profile


@pytest.mark.django_db
def test_pricing_page_shows_platform_counts(client):
    club = SocialClub.objects.create(
        name="CSC Pricing",
        email="pricing@example.com",
        street_address="Street 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49123",
        is_active=True,
        is_approved=True,
    )
    user = User.objects.create_user(
        email="pricing-member@example.com",
        password="StrongPass123!",
        first_name="Price",
        last_name="Member",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=880001,
        monthly_counter_key="2026-04",
    )

    response = client.get(reverse("core:pricing"))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Mitglieder gesamt" in html
    assert "Social Clubs aktiv" in html
    assert "0,50 EUR" in html
    assert reverse("core:social_club_register") in html
