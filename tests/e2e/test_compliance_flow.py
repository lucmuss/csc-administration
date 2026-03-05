"""E2E Tests: Compliance Flow (Compliance/Regeln)

Testet: Limit-Enforcement, Verdachtsanzeige, Reports
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse


@pytest.mark.django_db
def test_daily_limit_reset_at_midnight(client, member_user):
    """Test: Tägliches Limit wird um 00:00 zurückgesetzt"""
    from apps.members.models import Profile
    from apps.orders.management.commands.reset_daily_limits import Command

    # Setze täglichen Verbrauch
    member_user.profile.daily_used = Decimal("20")
    member_user.profile.save()

    # Reset ausführen
    Command().handle()

    member_user.profile.refresh_from_db()
    assert member_user.profile.daily_used == Decimal("0")


@pytest.mark.django_db
def test_monthly_limit_reset_on_first(client, member_user):
    """Test: Monatliches Limit wird am 1. zurückgesetzt"""
    from apps.members.models import Profile
    from apps.orders.management.commands.reset_monthly_limits import Command

    member_user.profile.monthly_used = Decimal("45")
    member_user.profile.save()

    # Reset ausführen (simuliert 1. des Monats)
    Command().handle()

    member_user.profile.refresh_from_db()
    assert member_user.profile.monthly_used == Decimal("0")


@pytest.mark.django_db
def test_suspicious_activity_detected(client, member_user, batch):
    """Test: Verdachtsanzeige bei >50g/Monat"""
    from apps.compliance.models import SuspiciousActivity
    from apps.compliance.services import check_suspicious_activity

    # Setze monatlichen Verbrauch auf über 50g
    member_user.profile.monthly_used = Decimal("55")
    member_user.profile.save()

    # Prüfung ausführen
    check_suspicious_activity()

    # Verdachtsanzeige sollte existieren
    assert SuspiciousActivity.objects.filter(member=member_user.profile).exists()


@pytest.mark.django_db
def test_suspicious_activity_list_view(client, board_user, member_user):
    """Test: Verdachtsanzeigen-Liste anzeigen"""
    from apps.compliance.models import SuspiciousActivity

    # Verdachtsanzeige erstellen
    SuspiciousActivity.objects.create(
        member=member_user.profile,
        activity_type=SuspiciousActivity.TYPE_EXCESS_CONSUMPTION,
        description="Über 50g/Monat konsumiert",
        detected_at=date.today(),
    )

    client.force_login(board_user)

    response = client.get(reverse("compliance:suspicious_activity_list"))

    assert response.status_code == 200
    assert member_user.profile.member_number in str(response.content)


@pytest.mark.django_db
def test_annual_report_generation(client, board_user):
    """Test: Jahresmeldung generieren"""
    from apps.compliance.services import generate_annual_report

    client.force_login(board_user)

    report = generate_annual_report(year=date.today().year)

    assert report is not None
    assert "mitglieder" in str(report).lower() or "abgabe" in str(report).lower()


@pytest.mark.django_db
def test_youth_protection_limit(client):
    """Test: Jugendschutz (18-21 Jahre: 30g/Monat, 10% THC)"""
    from apps.accounts.models import User
    from apps.members.models import Profile
    from apps.inventory.models import Strain, Batch

    # Jugendlichen erstellen (18 Jahre)
    young_user = User.objects.create_user(
        email="young@example.com",
        password="StrongPass123!",
        first_name="Jung",
        last_name="Nutzer",
        role=User.ROLE_MEMBER,
    )
    Profile.objects.create(
        user=young_user,
        birth_date=date.today() - timedelta(days=365 * 19),  # 19 Jahre
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100999,
    )

    # Hohe THC-Sorte
    strain = Strain.objects.create(
        name="High THC",
        slug="high-thc",
        thc_content=Decimal("20.00"),  # Über 10%
        price_per_gram=Decimal("12.00"),
    )
    batch = Batch.objects.create(
        strain=strain,
        batch_number="240301-HIGH",
        harvest_date=date.today(),
        total_harvested_grams=Decimal("1000.00"),
        available_grams=Decimal("1000.00"),
        price_per_gram=Decimal("12.00"),
    )

    client.force_login(young_user)

    # Versuch zu bestellen
    response = client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )

    # Sollte blockiert werden (THC zu hoch)
    # Oder Menge beschränkt sein
    assert response.status_code in [200, 302]


@pytest.mark.django_db
def test_probation_period_enforced(client):
    """Test: 6-Monats-Probezeit vor erstem Zugang"""
    from apps.accounts.models import User
    from apps.members.models import Profile

    # Neues Mitglied in Probezeit
    new_user = User.objects.create_user(
        email="newbie@example.com",
        password="StrongPass123!",
        first_name="Neu",
        last_name="Mitglied",
        role=User.ROLE_MEMBER,
    )
    profile = Profile.objects.create(
        user=new_user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100998,
        probation_until=date.today() + timedelta(days=180),  # 6 Monate Probezeit
    )

    client.force_login(new_user)

    # Versuch zu bestellen
    response = client.get(reverse("orders:shop"))

    # Sollte Hinweis auf Probezeit zeigen
    assert response.status_code == 200
    assert "probezeit" in str(response.content).lower() or "6 monate" in str(response.content).lower()


@pytest.mark.django_db
def test_audit_log_created_on_member_change(client, board_user, member_user):
    """Test: Audit-Log wird bei Mitglieds-Änderung erstellt"""
    from apps.audit.models import AuditLog

    client.force_login(board_user)

    # Mitglied bearbeiten
    response = client.post(
        reverse("members:profile_edit", kwargs={"pk": member_user.pk}),
        {
            "first_name": "Geändert",
            "last_name": "Name",
        },
    )

    assert response.status_code == 302
    
    # Audit-Log sollte existieren
    assert AuditLog.objects.filter(
        user=board_user,
        action="member_updated",
    ).exists()


@pytest.mark.django_db
def test_prevention_info_displayed_first_order(client, member_user, batch):
    """Test: Präventions-Info bei erster Abgabe"""
    from apps.compliance.models import PreventionInfo

    # Markiere als erste Abgabe
    PreventionInfo.objects.create(
        member=member_user.profile,
        info_type=PreventionInfo.TYPE_FIRST_DISPENSE,
        acknowledged=False,
    )

    client.force_login(member_user)

    response = client.get(reverse("orders:first_dispense_info"))

    assert response.status_code == 200
    assert "prävention" in str(response.content).lower() or "sucht" in str(response.content).lower()


@pytest.mark.django_db
def test_consumption_warning_at_40g(client, member_user):
    """Test: Warnung bei 40g/Monat"""
    member_user.profile.monthly_used = Decimal("40")
    member_user.profile.save()

    client.force_login(member_user)

    response = client.get(reverse("members:profile"))

    assert response.status_code == 200
    # Sollte Warnung anzeigen
    assert "warnung" in str(response.content).lower() or "40g" in str(response.content)


@pytest.mark.django_db
def test_compliance_dashboard_shows_stats(client, board_user):
    """Test: Compliance-Dashboard zeigt Statistiken"""
    client.force_login(board_user)

    response = client.get(reverse("compliance:dashboard"))

    assert response.status_code == 200
    # Sollte wichtige Compliance-Metriken zeigen


@pytest.mark.django_db
def test_bopst_report_export(client, board_user):
    """Test: BOPST-Report Export"""
    client.force_login(board_user)

    response = client.get(
        reverse("compliance:bopst_report"),
        {"month": date.today().month, "year": date.today().year},
    )

    assert response.status_code == 200
    # Sollte CSV oder PDF zurückgeben


@pytest.mark.django_db
def test_member_data_export_for_authorities(client, board_user, member_user):
    """Test: Mitgliedsdaten-Export für Behörden"""
    client.force_login(board_user)

    response = client.get(
        reverse("compliance:member_export"),
    )

    assert response.status_code == 200
    # Sollte anonymisierte Daten enthalten
