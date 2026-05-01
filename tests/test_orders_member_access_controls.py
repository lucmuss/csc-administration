from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import SocialClub
from apps.inventory.models import Strain
from apps.members.models import Profile


@pytest.fixture
def pending_member_user(db):
    user = get_user_model().objects.create_user(
        email="pending-member@example.com",
        password="StrongPass123!",
        first_name="Pending",
        last_name="Member",
        role=User.ROLE_MEMBER,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1994, 1, 1),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    return user


@pytest.mark.django_db
@override_settings(ENFORCE_ONBOARDING_REDIRECT_IN_TESTS=True)
def test_unverified_member_is_redirected_from_shop(client, pending_member_user):
    client.force_login(pending_member_user)
    response = client.get(reverse("orders:shop"))
    assert response.status_code == 302
    assert response.url == reverse("members:onboarding")


@pytest.mark.django_db
def test_add_to_cart_rejects_invalid_quantity(client, member_user):
    strain = Strain.objects.create(
        name="Bad Qty",
        thc=Decimal("15.00"),
        cbd=Decimal("0.20"),
        price=Decimal("9.00"),
        stock=Decimal("10.00"),
        is_active=True,
    )
    client.force_login(member_user)

    response = client.post(reverse("orders:add_to_cart"), data={"strain_id": str(strain.id), "quantity": "-2"}, follow=True)

    assert response.status_code == 200
    assert "Ungueltige Menge" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_add_to_cart_rejects_product_from_other_club_scope(client, member_user):
    club_a = SocialClub.objects.create(
        name="Club A",
        email="a@example.com",
        street_address="A-Str 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49110000001",
        is_active=True,
        is_approved=True,
    )
    club_b = SocialClub.objects.create(
        name="Club B",
        email="b@example.com",
        street_address="B-Str 1",
        postal_code="10115",
        city="Berlin",
        phone="+49110000002",
        is_active=True,
        is_approved=True,
    )
    member_user.social_club = club_a
    member_user.save(update_fields=["social_club"])

    foreign_strain = Strain.objects.create(
        name="Foreign Club Strain",
        thc=Decimal("18.00"),
        cbd=Decimal("0.40"),
        price=Decimal("11.00"),
        stock=Decimal("50.00"),
        is_active=True,
        social_club=club_b,
    )

    client.force_login(member_user)
    response = client.post(
        reverse("orders:add_to_cart"),
        data={"strain_id": str(foreign_strain.id), "quantity": "1"},
        follow=True,
    )

    assert response.status_code == 200
    assert "Produkt nicht verfuegbar" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_checkout_rejects_empty_cart(client, member_user):
    client.force_login(member_user)
    response = client.post(reverse("orders:checkout"), data={"confirm": "yes"}, follow=True)
    assert response.status_code == 200
    assert "Warenkorb ist leer" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_member_cannot_access_other_members_order_detail(client, member_user):
    other = get_user_model().objects.create_user(
        email="other-order-member@example.com",
        password="StrongPass123!",
        first_name="Other",
        last_name="Member",
        role=User.ROLE_MEMBER,
    )
    Profile.objects.create(
        user=other,
        birth_date=date(1991, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        balance=Decimal("200.00"),
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )

    strain = Strain.objects.create(
        name="Order Detail Test",
        thc=Decimal("12.00"),
        cbd=Decimal("0.10"),
        price=Decimal("7.00"),
        stock=Decimal("100.00"),
        is_active=True,
    )
    from apps.orders.services import CartLine, create_reserved_order

    other_order = create_reserved_order(user=other, cart_lines=[CartLine(strain_id=strain.id, quantity=Decimal("1"))])

    client.force_login(member_user)
    response = client.get(reverse("orders:detail", args=[other_order.id]))
    assert response.status_code == 404
