from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth.models import AnonymousUser

from apps.accounts.models import User
from apps.core.models import SocialClub
from apps.members.models import Profile


def _create_club(name: str) -> SocialClub:
    return SocialClub.objects.create(
        name=name,
        email=f"{name.lower().replace(' ', '-') }@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49123",
        is_active=True,
        is_approved=True,
    )


@pytest.mark.django_db
def test_user_manager_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="StrongPass123!", first_name="A", last_name="B")


@pytest.mark.django_db
def test_user_manager_create_superuser_sets_required_flags():
    user = User.objects.create_superuser(
        email="super@example.com",
        password="StrongPass123!",
        first_name="Super",
        last_name="User",
    )

    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.role == User.ROLE_BOARD


@pytest.mark.django_db
def test_user_manager_create_superuser_rejects_invalid_flags():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="bad-super@example.com",
            password="StrongPass123!",
            first_name="Bad",
            last_name="Super",
            is_staff=False,
        )


@pytest.mark.django_db
def test_user_full_name_string_and_ordering():
    user_b = User.objects.create_user(email="b@example.com", password="StrongPass123!", first_name="B", last_name="Beta")
    user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!", first_name="A", last_name="Alpha")

    assert user_a.full_name == "A Alpha"
    assert str(user_a) == "a@example.com"
    assert list(User.objects.values_list("email", flat=True)[:2]) == ["a@example.com", "b@example.com"]
    assert User.REQUIRED_FIELDS == ["first_name", "last_name"]
    assert User.USERNAME_FIELD == "email"
    assert user_b.full_name == "B Beta"


@pytest.mark.django_db
def test_user_messaging_permissions_for_staff_and_board():
    staff = User.objects.create_user(
        email="staff-msg@example.com",
        password="StrongPass123!",
        first_name="Staff",
        last_name="One",
        role=User.ROLE_STAFF,
        is_staff=True,
    )
    board = User.objects.create_user(
        email="board-msg@example.com",
        password="StrongPass123!",
        first_name="Board",
        last_name="One",
        role=User.ROLE_BOARD,
        is_staff=True,
    )

    assert staff.has_perm("messaging.view_massemail") is True
    assert staff.has_module_perms("messaging") is True
    assert board.has_perm("messaging.change_massemail") is True
    assert board.has_module_perms("messaging") is True


@pytest.mark.django_db
def test_user_messaging_permissions_for_member_and_anonymous():
    member = User.objects.create_user(
        email="member-msg@example.com",
        password="StrongPass123!",
        first_name="Member",
        last_name="One",
        role=User.ROLE_MEMBER,
    )

    assert member.has_module_perms("messaging") is False
    assert member.has_perm("messaging.view_massemail") is False
    assert AnonymousUser().is_authenticated is False


@pytest.mark.django_db
def test_user_social_club_fk_is_set_null_on_delete():
    club = _create_club("CSC FK Club")
    user = User.objects.create_user(
        email="fk-user@example.com",
        password="StrongPass123!",
        first_name="FK",
        last_name="User",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key="2026-05",
    )

    club.delete()
    user.refresh_from_db()
    assert user.social_club is None
