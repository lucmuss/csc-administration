from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.members.models import Profile
from apps.orders.models import Order

from .models import ComplianceReport, PreventionInfo, SuspiciousActivity


def _month_key(day: date) -> str:
    return day.strftime("%Y-%m")


def reset_daily_limits(target_date: date | None = None) -> int:
    target_date = target_date or timezone.localdate()
    updated = Profile.objects.exclude(daily_counter_date=target_date).update(
        daily_used=Decimal("0.00"),
        daily_counter_date=target_date,
    )
    return updated


def reset_monthly_limits(target_date: date | None = None) -> int:
    target_date = target_date or timezone.localdate()
    month_key = _month_key(target_date)
    updated = Profile.objects.exclude(monthly_counter_key=month_key).update(
        monthly_used=Decimal("0.00"),
        monthly_counter_key=month_key,
    )
    return updated


def detect_suspicious_activity_for_profile(profile: Profile, threshold: Decimal = Decimal("50.00")) -> SuspiciousActivity | None:
    if profile.monthly_used <= threshold:
        return None

    activity, _ = SuspiciousActivity.objects.update_or_create(
        profile=profile,
        month_key=profile.monthly_counter_key,
        defaults={
            "consumed_grams": profile.monthly_used,
            "threshold_grams": threshold,
        },
    )
    return activity


def detect_suspicious_activity(target_date: date | None = None, threshold: Decimal = Decimal("50.00")) -> int:
    target_date = target_date or timezone.localdate()
    month_key = _month_key(target_date)

    profiles = Profile.objects.filter(monthly_counter_key=month_key, monthly_used__gt=threshold)
    created_or_updated = 0
    for profile in profiles:
        detect_suspicious_activity_for_profile(profile=profile, threshold=threshold)
        created_or_updated += 1
    return created_or_updated


def ensure_prevention_info_for_first_dispense(*, user, order: Order) -> PreventionInfo | None:
    profile = Profile.objects.filter(user=user).first()
    if not profile:
        return None

    if hasattr(profile, "prevention_info"):
        return profile.prevention_info

    has_previous_dispense = (
        Order.objects.filter(member=user)
        .exclude(id=order.id)
        .exclude(status=Order.STATUS_CANCELLED)
        .exists()
    )
    if has_previous_dispense:
        return None

    return PreventionInfo.objects.create(profile=profile, first_order=order)


def generate_annual_report(*, year: int, generated_by=None) -> ComplianceReport:
    orders_qs = Order.objects.filter(created_at__year=year).exclude(status=Order.STATUS_CANCELLED)

    order_stats = orders_qs.aggregate(
        total_orders=Count("id"),
        total_members=Count("member_id", distinct=True),
        total_grams=Sum("total_grams"),
    )

    monthly_stats_qs = (
        orders_qs.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total_orders=Count("id"), total_grams=Sum("total_grams"))
        .order_by("month")
    )
    monthly_stats = [
        {
            "month": row["month"].date().isoformat() if row["month"] else None,
            "total_orders": row["total_orders"],
            "total_grams": str(row["total_grams"] or Decimal("0.00")),
        }
        for row in monthly_stats_qs
    ]

    suspicious_cases = SuspiciousActivity.objects.filter(month_key__startswith=f"{year}-").count()

    report, _ = ComplianceReport.objects.update_or_create(
        year=year,
        defaults={
            "generated_by": generated_by,
            "total_orders": order_stats["total_orders"] or 0,
            "total_members": order_stats["total_members"] or 0,
            "total_grams": order_stats["total_grams"] or Decimal("0.00"),
            "suspicious_cases": suspicious_cases,
            "report_data": {
                "year": year,
                "generated_at": timezone.now().isoformat(),
                "monthly_stats": monthly_stats,
            },
        },
    )

    return report
