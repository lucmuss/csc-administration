from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import Strain
from apps.members.models import Profile


@pytest.mark.django_db
def test_members_directory_sanitizes_query_and_redirects(client, member_user):
    member_user.role = User.ROLE_STAFF
    member_user.is_staff = True
    member_user.save(update_fields=["role", "is_staff"])

    client.force_login(member_user)
    response = client.get(reverse("members:directory"), {"q": "<script>alert(1)</script> OR 1=1"})

    assert response.status_code == 302
    assert "<" not in response.url
    assert ">" not in response.url


@pytest.mark.django_db
def test_order_cancel_requires_post(client, member_user):
    response = client.get(reverse("orders:cancel", args=[12345]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_csrf_protection_blocks_post_without_token(member_user):
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(member_user)

    response = csrf_client.post(reverse("orders:checkout"), data={"confirm": "yes"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_member_cannot_open_admin_order_list(client, member_user):
    client.force_login(member_user)
    response = client.get(reverse("orders:admin_list"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_idor_protection_member_profile_detail_other_user_redirects(client, member_user):
    other = get_user_model().objects.create_user(
        email="idor-other@example.com",
        password="StrongPass123!",
        first_name="I",
        last_name="Dor",
        role=User.ROLE_MEMBER,
    )
    other_profile = Profile.objects.create(
        user=other,
        birth_date=date(1990, 2, 2),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )

    client.force_login(member_user)
    response = client.get(reverse("members:detail", args=[other_profile.id]))
    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")


@pytest.mark.django_db
def test_cart_ignores_invalid_session_payload_instead_of_crashing(client, member_user):
    client.force_login(member_user)
    session = client.session
    session["cart"] = {"not-an-id": "aaa", "999999": "2"}
    session.save()

    response = client.get(reverse("orders:cart"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_checkout_handles_sqlish_quantity_input_gracefully(client, member_user):
    strain = Strain.objects.create(
        name="Security Strain",
        thc=Decimal("20.00"),
        cbd=Decimal("0.20"),
        price=Decimal("10.00"),
        stock=Decimal("10.00"),
        is_active=True,
    )
    client.force_login(member_user)

    response = client.post(
        reverse("orders:add_to_cart"),
        data={"strain_id": str(strain.id), "quantity": "1; DROP TABLE users;"},
        follow=True,
    )

    assert response.status_code == 200
    assert "Ungueltige Menge" in response.content.decode("utf-8")
