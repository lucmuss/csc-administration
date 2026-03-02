from datetime import date
from decimal import Decimal

import pytest


@pytest.mark.django_db
def test_daily_limit_enforced():
    from apps.accounts.models import User
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="limit1@example.com",
        password="StrongPass123!",
        first_name="Daily",
        last_name="Limit",
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        daily_used=Decimal("24.00"),
        monthly_used=Decimal("40.00"),
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    allowed, reason = profile.can_consume(Decimal("2.00"))
    assert not allowed
    assert "Tageslimit" in reason


@pytest.mark.django_db
def test_monthly_limit_enforced():
    from apps.accounts.models import User
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="limit2@example.com",
        password="StrongPass123!",
        first_name="Monthly",
        last_name="Limit",
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        daily_used=Decimal("5.00"),
        monthly_used=Decimal("49.00"),
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    allowed, reason = profile.can_consume(Decimal("2.00"))
    assert not allowed
    assert "Monatslimit" in reason
