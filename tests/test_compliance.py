from decimal import Decimal
from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.finance.models import SepaMandate
from apps.members.models import Profile


@pytest.fixture
def board_user(db):
    user = User.objects.create_user(
        email="board-compliance@example.com",
        password="StrongPass123!",
        first_name="Bea",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1985, 5, 5),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100500,
        desired_join_date=date(2026, 4, 1),
        street_address="Vorstandsweg 5",
        postal_code="04107",
        city="Leipzig",
        phone="+491701234567",
        bank_name="GLS Bank",
        account_holder_name="Bea Board",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        registration_completed_at=timezone.now(),
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Bea Board",
        mandate_reference="CSC-FIXTURE-BOARD",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


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


@pytest.mark.django_db
def test_annual_report_csv_export_downloads(client, board_user):
    client.force_login(board_user)

    response = client.get(reverse("compliance:annual_report"), {"year": timezone.localdate().year, "format": "csv"})

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert "attachment;" in response["Content-Disposition"]
    content = response.content.decode("utf-8")
    assert "Kennzahl,Wert" in content
    assert "Monat,Abgaben,Gesamtmenge (g)" in content
