from decimal import Decimal

import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_suspicious_activity_created_for_monthly_usage_above_50g(member_user):
    from apps.compliance.models import SuspiciousActivity
    from apps.compliance.services import detect_suspicious_activity
    from apps.members.models import Profile

    profile = Profile.objects.get(user=member_user)
    profile.monthly_used = Decimal("55.00")
    profile.monthly_counter_key = timezone.localdate().strftime("%Y-%m")
    profile.save(update_fields=["monthly_used", "monthly_counter_key"])

    detected = detect_suspicious_activity()

    assert detected == 1
    activity = SuspiciousActivity.objects.get(profile=profile, month_key=profile.monthly_counter_key)
    assert activity.consumed_grams == Decimal("55.00")
    assert activity.threshold_grams == Decimal("50.00")


@pytest.mark.django_db
def test_annual_report_generation_aggregates_orders_and_suspicious_cases(member_user):
    from apps.compliance.models import SuspiciousActivity
    from apps.compliance.services import generate_annual_report
    from apps.members.models import Profile
    from apps.orders.models import Order

    year = timezone.localdate().year
    profile = Profile.objects.get(user=member_user)

    Order.objects.create(
        member=member_user,
        status=Order.STATUS_COMPLETED,
        total=Decimal("100.00"),
        total_grams=Decimal("10.00"),
        reserved_until=timezone.now(),
        paid_with_balance=Decimal("100.00"),
    )
    Order.objects.create(
        member=member_user,
        status=Order.STATUS_CANCELLED,
        total=Decimal("50.00"),
        total_grams=Decimal("5.00"),
        reserved_until=timezone.now(),
        paid_with_balance=Decimal("50.00"),
    )

    SuspiciousActivity.objects.create(
        profile=profile,
        month_key=f"{year}-01",
        consumed_grams=Decimal("60.00"),
        threshold_grams=Decimal("50.00"),
    )

    report = generate_annual_report(year=year)

    assert report.year == year
    assert report.total_orders == 1
    assert report.total_members == 1
    assert report.total_grams == Decimal("10.00")
    assert report.suspicious_cases == 1
    assert isinstance(report.report_data.get("monthly_stats"), list)
