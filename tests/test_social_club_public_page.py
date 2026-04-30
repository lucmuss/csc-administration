from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.models import User
from apps.core.models import PublicDocument, SocialClub, SocialClubOpeningHour, SocialClubReview
from apps.inventory.models import Strain
from apps.members.models import Profile


@pytest.mark.django_db
def test_public_social_club_detail_shows_statute_and_reviews(client):
    club = SocialClub.objects.create(
        name="CSC Public Leipzig",
        email="public@example.com",
        street_address="Public Str. 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49123",
        public_description="Wir sind ein demokratisch organisierter Social Club in Leipzig.",
        is_active=True,
        is_approved=True,
    )
    PublicDocument.objects.create(
        social_club=club,
        title="Satzung 2026",
        category=PublicDocument.CATEGORY_STATUTE,
        description="Aktuelle Vereinssatzung",
        file=SimpleUploadedFile("satzung.txt", b"satzung", content_type="text/plain"),
        is_public=True,
    )
    reviewer = User.objects.create_user(
        email="reviewer-public@example.com",
        password="StrongPass123!",
        first_name="Anna",
        last_name="Bewertet",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    Profile.objects.create(
        user=reviewer,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=991001,
        monthly_counter_key="2026-04",
    )
    SocialClubReview.objects.create(social_club=club, user=reviewer, rating=5, comment="Sehr gut organisiert")
    SocialClubOpeningHour.objects.create(social_club=club, weekday=0, starts_at="14:00", ends_at="18:00")
    SocialClubOpeningHour.objects.create(social_club=club, weekday=2, starts_at="10:00", ends_at="12:00")
    Strain.objects.create(
        name="Lemon Tree",
        thc=20,
        cbd=1,
        price=9.5,
        stock=120,
        is_active=True,
    )

    response = client.get(reverse("core:social_club_public_detail", args=[club.slug]))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "CSC Public Leipzig" in html
    assert "Satzung 2026" in html
    assert "5 / 5 Sterne" in html
    assert "Sehr gut organisiert" in html
    assert "Verifizierte Mitglieder" in html
    assert "1 / 500" in html
    assert "Sorten im Shop" in html
    assert "Cannabis-Ausgabe im Wochenplan" in html
    assert "14:00 - 18:00" in html


@pytest.mark.django_db
def test_public_social_club_list_is_publicly_accessible(client):
    SocialClub.objects.create(
        name="CSC Public A",
        email="a@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49111",
        is_active=True,
        is_approved=True,
    )

    response = client.get(reverse("core:social_club_public_list"))

    assert response.status_code == 200
    assert "Social Clubs auf der Plattform" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_public_social_club_list_supports_average_price_filter(client):
    SocialClub.objects.create(
        name="CSC Price Low",
        email="low@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49111",
        avg_strain_price="6.50",
        min_strain_price="5.00",
        max_strain_price="8.00",
        is_active=True,
        is_approved=True,
    )
    SocialClub.objects.create(
        name="CSC Price High",
        email="high@example.com",
        street_address="B",
        postal_code="04109",
        city="Leipzig",
        phone="+49222",
        avg_strain_price="12.00",
        min_strain_price="11.00",
        max_strain_price="14.00",
        is_active=True,
        is_approved=True,
    )

    response = client.get(reverse("core:social_club_public_list"), {"price_min": "10", "price_max": "13"})
    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "CSC Price High" in html
    assert "CSC Price Low" not in html
