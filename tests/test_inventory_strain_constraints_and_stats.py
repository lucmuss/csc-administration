from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.core.models import SocialClub
from apps.inventory.forms import StrainForm
from apps.inventory.models import Strain


@pytest.mark.django_db
def test_strain_name_unique_per_social_club():
    club = SocialClub.objects.create(
        name="CSC Unique Club",
        email="u@example.com",
        street_address="U-Str 1",
        postal_code="04109",
        city="Leipzig",
        phone="+491616",
        is_active=True,
        is_approved=True,
    )
    Strain.objects.create(
        social_club=club,
        name="Orange Bud",
        thc=Decimal("18.00"),
        cbd=Decimal("0.10"),
        price=Decimal("8.00"),
        stock=Decimal("5.00"),
    )

    with pytest.raises(IntegrityError):
        Strain.objects.create(
            social_club=club,
            name="Orange Bud",
            thc=Decimal("18.00"),
            cbd=Decimal("0.10"),
            price=Decimal("8.00"),
            stock=Decimal("5.00"),
        )


@pytest.mark.django_db
def test_strain_name_can_repeat_in_different_social_clubs():
    c1 = SocialClub.objects.create(
        name="Club One",
        email="one@example.com",
        street_address="1",
        postal_code="04109",
        city="Leipzig",
        phone="+491717",
        is_active=True,
        is_approved=True,
    )
    c2 = SocialClub.objects.create(
        name="Club Two",
        email="two@example.com",
        street_address="2",
        postal_code="10115",
        city="Berlin",
        phone="+491818",
        is_active=True,
        is_approved=True,
    )

    s1 = Strain.objects.create(social_club=c1, name="Lemon Haze", thc=18, cbd=0.2, price=9, stock=10)
    s2 = Strain.objects.create(social_club=c2, name="Lemon Haze", thc=20, cbd=0.1, price=11, stock=8)

    assert s1.id != s2.id


@pytest.mark.django_db
def test_social_club_price_stats_refresh_on_create_update_delete():
    club = SocialClub.objects.create(
        name="Stats Club",
        email="stats@example.com",
        street_address="3",
        postal_code="04109",
        city="Leipzig",
        phone="+491919",
        is_active=True,
        is_approved=True,
    )
    s1 = Strain.objects.create(social_club=club, name="A", thc=18, cbd=0.1, price=Decimal("8.00"), stock=10)
    s2 = Strain.objects.create(social_club=club, name="B", thc=19, cbd=0.2, price=Decimal("12.00"), stock=10)
    club.refresh_from_db()
    assert club.min_strain_price == Decimal("8.00")
    assert club.max_strain_price == Decimal("12.00")
    assert club.avg_strain_price == Decimal("10.00")

    s1.price = Decimal("10.00")
    s1.save(update_fields=["price"])
    club.refresh_from_db()
    assert club.min_strain_price == Decimal("10.00")
    assert club.max_strain_price == Decimal("12.00")
    assert club.avg_strain_price == Decimal("11.00")

    s2.delete()
    club.refresh_from_db()
    assert club.min_strain_price == Decimal("10.00")
    assert club.max_strain_price == Decimal("10.00")
    assert club.avg_strain_price == Decimal("10.00")


@pytest.mark.django_db
def test_strain_form_accepts_optional_cannabinoids():
    form = StrainForm(
        data={
            "name": "Chem Cookies",
            "product_type": Strain.PRODUCT_TYPE_FLOWER,
            "card_tone": Strain.CARD_TONE_APRICOT,
            "thc": "21.5",
            "cbd": "0.5",
            "cbg": "0.2",
            "cbn": "0.1",
            "cbc": "0.1",
            "cbv": "0.0",
            "price": "12.50",
            "stock": "35",
            "quality_grade": Strain.QUALITY_A,
            "is_active": "on",
        }
    )

    assert form.is_valid(), form.errors
