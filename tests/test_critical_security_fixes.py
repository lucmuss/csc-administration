from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.core.models import SocialClub
from apps.inventory.models import InventoryItem, InventoryLocation, Strain
from apps.members.models import Profile


pytestmark = pytest.mark.django_db


def _create_club(name: str, email: str) -> SocialClub:
    return SocialClub.objects.create(
        name=name,
        email=email,
        street_address="Testweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49123456789",
        federal_state=SocialClub.BUNDESLAND_SN,
        is_active=True,
        is_approved=True,
    )


def _create_board(email: str, club: SocialClub) -> User:
    user = User.objects.create_user(
        email=email,
        password="StrongPass123!",
        first_name="Board",
        last_name="User",
        role=User.ROLE_BOARD,
        is_staff=True,
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1985, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key="2026-05",
    )
    return user


def _create_member(email: str, club: SocialClub) -> User:
    user = User.objects.create_user(
        email=email,
        password="StrongPass123!",
        first_name="Member",
        last_name="User",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        monthly_counter_key="2026-05",
    )
    return user


def test_legacy_member_views_are_scoped_to_actor_social_club(client):
    club_a = _create_club("Club A", "club-a@example.com")
    club_b = _create_club("Club B", "club-b@example.com")
    board_a = _create_board("board-a@example.com", club_a)
    member_b = _create_member("member-b@example.com", club_b)

    client.force_login(board_a)
    response = client.get(reverse("members:approve", args=[member_b.id]))

    assert response.status_code == 404


def test_inventory_count_form_requires_board_role(client):
    club = _create_club("Inventory Club", "inventory-club@example.com")
    member = _create_member("inventory-member@example.com", club)
    strain = Strain.objects.create(
        social_club=club,
        name="Sorte A",
        thc=Decimal("10.00"),
        cbd=Decimal("1.00"),
        price=Decimal("8.00"),
        stock=Decimal("100.00"),
    )
    location = InventoryLocation.objects.create(name="Regal 1", type=InventoryLocation.TYPE_SHELF)
    InventoryItem.objects.create(strain=strain, location=location, quantity=Decimal("100.00"))

    client.force_login(member)
    response = client.get(reverse("inventory:inventory_count_form"))

    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")


@override_settings(DEBUG=False)
def test_media_route_not_served_by_django_when_debug_is_false(client):
    response = client.get("/media/non-existent-sensitive-file.pdf")
    assert response.status_code == 404


def test_strain_model_rejects_invalid_cannabinoid_ranges():
    club = _create_club("Range Club", "range@example.com")
    strain = Strain(
        social_club=club,
        name="Invalid THC",
        thc=Decimal("120.00"),
        cbd=Decimal("1.00"),
        price=Decimal("7.50"),
        stock=Decimal("20.00"),
    )
    with pytest.raises(ValidationError):
        strain.save()
