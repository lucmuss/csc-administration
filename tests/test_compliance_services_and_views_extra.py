from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.compliance.models import SuspiciousActivity
from apps.compliance.services import (
    detect_suspicious_activity_for_profile,
    ensure_prevention_info_for_first_dispense,
    generate_annual_report,
    reset_daily_limits,
    reset_monthly_limits,
)
from apps.members.models import Profile
from apps.orders.models import Order


@pytest.fixture
def board_user(db):
    user = User.objects.create_user(
        email="comp-board@example.com",
        password="StrongPass123!",
        first_name="Comp",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    Profile.objects.create(
        user=user,
        birth_date=timezone.datetime(1988, 1, 1).date(),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    return user


@pytest.mark.django_db
def test_reset_limits_updates_changed_profiles(member_user):
    profile = member_user.profile
    profile.daily_counter_date = timezone.localdate() - timedelta(days=1)
    profile.monthly_counter_key = "1999-01"
    profile.daily_used = Decimal("10")
    profile.monthly_used = Decimal("20")
    profile.save()

    assert reset_daily_limits(timezone.localdate()) >= 1
    assert reset_monthly_limits(timezone.localdate()) >= 1

    profile.refresh_from_db()
    assert profile.daily_used == Decimal("0.00")
    assert profile.monthly_used == Decimal("0.00")


@pytest.mark.django_db
def test_detect_suspicious_activity_for_profile_creates_entry(member_user):
    profile = member_user.profile
    profile.monthly_used = Decimal("20.00")
    profile.monthly_counter_key = timezone.localdate().strftime("%Y-%m")
    profile.save(update_fields=["monthly_used", "monthly_counter_key", "updated_at"])

    activity = detect_suspicious_activity_for_profile(profile=profile, threshold=Decimal("10.00"))

    assert activity is not None
    assert SuspiciousActivity.objects.filter(profile=profile).exists()


@pytest.mark.django_db
def test_ensure_prevention_info_for_first_dispense_only_once(member_user):
    order = Order.objects.create(
        member=member_user,
        status=Order.STATUS_RESERVED,
        total=Decimal("10.00"),
        total_grams=Decimal("1.00"),
        reserved_until=timezone.now() + timedelta(hours=1),
    )

    info = ensure_prevention_info_for_first_dispense(user=member_user, order=order)
    assert info is not None

    second = ensure_prevention_info_for_first_dispense(user=member_user, order=order)
    assert second.id == info.id


@pytest.mark.django_db
def test_generate_annual_report_returns_expected_payload(board_user):
    report = generate_annual_report(year=timezone.localdate().year, generated_by=board_user)
    assert report.year == timezone.localdate().year
    assert "monthly_stats" in report.report_data


@pytest.mark.django_db
def test_compliance_dashboard_requires_board(client, member_user):
    client.force_login(member_user)
    response = client.get(reverse("compliance:dashboard"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_annual_report_csv_for_board(client, board_user):
    client.force_login(board_user)
    response = client.get(reverse("compliance:annual_report"), {"year": timezone.localdate().year, "format": "csv"})
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
