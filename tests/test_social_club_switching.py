from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.models import User
from apps.core.models import PublicDocument, SocialClub
from apps.members.models import Profile


@pytest.mark.django_db
def test_switch_social_club_sets_cookie_and_filters_documents(client):
    club_a = SocialClub.objects.create(
        name="CSC Alpha",
        email="alpha@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49111",
        is_approved=True,
        is_active=True,
    )
    club_b = SocialClub.objects.create(
        name="CSC Beta",
        email="beta@example.com",
        street_address="B",
        postal_code="04109",
        city="Leipzig",
        phone="+49222",
        is_approved=True,
        is_active=True,
    )
    PublicDocument.objects.create(
        social_club=club_a,
        title="Alpha Satzung",
        category=PublicDocument.CATEGORY_STATUTE,
        file=SimpleUploadedFile("alpha.txt", b"a", content_type="text/plain"),
        is_public=True,
    )
    PublicDocument.objects.create(
        social_club=club_b,
        title="Beta Satzung",
        category=PublicDocument.CATEGORY_STATUTE,
        file=SimpleUploadedFile("beta.txt", b"b", content_type="text/plain"),
        is_public=True,
    )

    response = client.post(reverse("core:social_club_switch"), data={"social_club_id": club_b.id, "next": reverse("core:documents")}, follow=True)
    assert response.status_code == 200
    assert response.client.cookies.get("active_social_club_id") is not None
    html = response.content.decode("utf-8")
    assert "Beta Satzung" in html
    assert "Alpha Satzung" not in html


@pytest.mark.django_db
def test_imprint_uses_selected_social_club_data(client):
    club = SocialClub.objects.create(
        name="CSC Legal",
        email="legal@example.com",
        street_address="Legalstr. 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49341234",
        board_representatives="Max Legal",
        register_court="Amtsgericht Leipzig",
        tax_number="123/456",
        is_approved=True,
        is_active=True,
    )
    client.post(reverse("core:social_club_switch"), data={"social_club_id": club.id, "next": reverse("core:imprint")})
    response = client.get(reverse("core:imprint"))

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "CSC Legal" in html
    assert "legal@example.com" in html
    assert "Amtsgericht Leipzig" in html
