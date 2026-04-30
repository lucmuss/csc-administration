from __future__ import annotations

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.accounts.models import User
from apps.core.forms import SocialClubOpeningHourForm
from apps.core.models import SocialClub, SocialClubOpeningHour, SocialClubReview
from apps.members.models import Profile


@pytest.mark.django_db
def test_social_club_slug_is_unique_with_collision_suffix():
    c1 = SocialClub.objects.create(
        name="CSC Leipzig Süd",
        email="a@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+491",
        is_active=True,
        is_approved=True,
    )
    c2 = SocialClub.objects.create(
        name="CSC Leipzig Sud",
        email="b@example.com",
        street_address="B",
        postal_code="04109",
        city="Leipzig",
        phone="+492",
        is_active=True,
        is_approved=True,
    )

    assert c1.slug
    assert c2.slug
    assert c1.slug != c2.slug


@pytest.mark.django_db
def test_opening_hour_form_rejects_end_before_start():
    form = SocialClubOpeningHourForm(
        data={
            "weekday": SocialClubOpeningHour.WEEKDAY_MONDAY,
            "starts_at": "18:00",
            "ends_at": "14:00",
        }
    )
    assert form.is_valid() is False
    assert "Endzeit" in str(form.errors)


@pytest.mark.django_db
def test_social_club_review_unique_per_user_and_club():
    club = SocialClub.objects.create(
        name="CSC Review Club",
        email="review@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+493",
        is_active=True,
        is_approved=True,
    )
    user = User.objects.create_user(
        email="review-user@example.com",
        password="StrongPass123!",
        first_name="Re",
        last_name="Viewer",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key="2026-04",
    )
    SocialClubReview.objects.create(social_club=club, user=user, rating=5)

    with pytest.raises(IntegrityError):
        SocialClubReview.objects.create(social_club=club, user=user, rating=4)
