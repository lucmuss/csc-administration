from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.inventory.models import InventoryItem, InventoryLocation, Strain
from apps.inventory.services import InventoryService
from apps.members.models import Profile


@pytest.mark.django_db
def test_inventory_move_stock_rejects_insufficient_quantity():
    strain = Strain.objects.create(name="Inv A", thc=18, cbd=0.2, price=8, stock=100)
    source = InventoryLocation.objects.create(name="Source", type=InventoryLocation.TYPE_SHELF, capacity=100)
    target = InventoryLocation.objects.create(name="Target", type=InventoryLocation.TYPE_SHELF, capacity=100)
    InventoryItem.objects.create(strain=strain, location=source, quantity=Decimal("2"))

    with pytest.raises(Exception):
        InventoryService.move_stock(strain=strain, source=source, target=target, quantity=Decimal("3"))


@pytest.mark.django_db
def test_inventory_count_form_rejects_decimal_count_input(client, member_user):
    member_user.role = User.ROLE_STAFF
    member_user.is_staff = True
    member_user.save(update_fields=["role", "is_staff"])
    strain = Strain.objects.create(name="Count A", thc=18, cbd=0.2, price=8, stock=100)
    location = InventoryLocation.objects.create(name="Count Loc", type=InventoryLocation.TYPE_SHELF, capacity=100)
    item = InventoryItem.objects.create(strain=strain, location=location, quantity=Decimal("5"))

    client.force_login(member_user)
    response = client.post(reverse("inventory:inventory_count_form"), data={f"item_{item.id}": "10.5"})

    assert response.status_code == 200
    assert "ganze Zahl" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_strain_detail_redirects_for_foreign_club(client, member_user):
    from apps.core.models import SocialClub

    club_a = SocialClub.objects.create(
        name="Club A2",
        email="a2@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+491",
        is_active=True,
        is_approved=True,
    )
    club_b = SocialClub.objects.create(
        name="Club B2",
        email="b2@example.com",
        street_address="B",
        postal_code="10115",
        city="Berlin",
        phone="+492",
        is_active=True,
        is_approved=True,
    )
    member_user.social_club = club_a
    member_user.save(update_fields=["social_club"])

    strain = Strain.objects.create(
        social_club=club_b,
        name="Foreign Strain",
        thc=18,
        cbd=0.2,
        price=8,
        stock=10,
        is_active=True,
    )

    client.force_login(member_user)
    response = client.get(reverse("inventory:strain_detail", args=[strain.id]))

    assert response.status_code == 302
    assert response.url == reverse("inventory:strain_list")
