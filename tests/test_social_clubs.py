from datetime import date

import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.core.models import SocialClub
from apps.members.models import Profile


@pytest.mark.django_db
def test_social_club_registration_creates_pending_admin(client):
    response = client.post(
        reverse("core:social_club_register"),
        data={
            "step": "club",
            "name": "CSC Test Leipzig",
            "email": "club@test.de",
            "street_address": "Testweg 1",
            "postal_code": "04109",
            "city": "Leipzig",
            "max_verified_members": "500",
            "phone": "+4917000000",
            "website": "https://example.org",
        },
        follow=True,
    )
    assert response.status_code == 200
    club = SocialClub.objects.get(name="CSC Test Leipzig")
    assert club.is_approved is False

    response = client.post(
        reverse("core:social_club_register"),
        data={
            "step": "admin",
            "first_name": "Club",
            "last_name": "Admin",
            "email": "admin@club-test.de",
            "birth_date": "1990-01-01",
            "password": "StrongPass123!",
        },
        follow=True,
    )
    assert response.status_code == 200
    user = User.objects.get(email="admin@club-test.de")
    assert user.is_active is False
    assert user.social_club_id == club.id
    assert user.role == User.ROLE_BOARD


@pytest.mark.django_db
def test_superadmin_can_approve_social_club(client):
    superadmin = User.objects.create_user(
        email="superadmin@example.com",
        password="StrongPass123!",
        first_name="Super",
        last_name="Admin",
        role=User.ROLE_BOARD,
        is_staff=True,
        is_superuser=True,
    )
    Profile.objects.create(
        user=superadmin,
        birth_date=date(1988, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=200001,
        monthly_counter_key="2026-04",
    )
    club = SocialClub.objects.create(
        name="CSC Pending",
        email="pending@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49111",
        is_approved=False,
        is_active=True,
    )
    pending_admin = User.objects.create_user(
        email="pending-admin@example.com",
        password="StrongPass123!",
        first_name="Pending",
        last_name="Admin",
        role=User.ROLE_BOARD,
        is_staff=True,
        is_active=False,
        social_club=club,
    )
    Profile.objects.create(
        user=pending_admin,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        monthly_counter_key="2026-04",
    )

    client.force_login(superadmin)
    response = client.post(reverse("core:social_club_admin"), data={"club_id": club.id, "action": "approve"}, follow=True)

    assert response.status_code == 200
    club.refresh_from_db()
    pending_admin.refresh_from_db()
    pending_admin.profile.refresh_from_db()
    assert club.is_approved is True
    assert pending_admin.is_active is True
    assert pending_admin.profile.is_verified is True


@pytest.mark.django_db
def test_login_rejects_wrong_social_club(client):
    club_a = SocialClub.objects.create(
        name="CSC A",
        email="a@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49111",
        is_approved=True,
        is_active=True,
    )
    club_b = SocialClub.objects.create(
        name="CSC B",
        email="b@example.com",
        street_address="B",
        postal_code="04109",
        city="Leipzig",
        phone="+49222",
        is_approved=True,
        is_active=True,
    )
    user = User.objects.create_user(
        email="member-club@example.com",
        password="StrongPass123!",
        first_name="Club",
        last_name="Member",
        role=User.ROLE_MEMBER,
        social_club=club_a,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=123456,
        monthly_counter_key="2026-04",
    )

    response = client.post(reverse("accounts:login"), data={"username": user.email, "password": "StrongPass123!", "social_club": club_b.id})
    assert response.status_code == 200
    assert "gehoert nicht zum ausgewaehlten Social Club" in response.content.decode("utf-8")
