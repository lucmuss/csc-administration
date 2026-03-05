"""E2E Tests: Admin Flow (Admin-Funktionen)

Testet: Dashboard, Einstellungen, Benutzerverwaltung
"""
import pytest
from datetime import date
from decimal import Decimal

from django.urls import reverse


@pytest.mark.django_db
def test_admin_dashboard_accessible(client, board_user):
    """Test: Admin-Dashboard zugänglich für Vorstand"""
    client.force_login(board_user)

    response = client.get(reverse("admin:dashboard"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_dashboard_shows_stats(client, board_user, member_user, invoice):
    """Test: Admin-Dashboard zeigt Statistiken"""
    client.force_login(board_user)

    response = client.get(reverse("admin:dashboard"))

    assert response.status_code == 200
    # Sollte wichtige Metriken zeigen
    assert str(member_user.profile.member_number) in str(response.content) or "mitglieder" in str(response.content).lower()


@pytest.mark.django_db
def test_staff_cannot_access_admin_dashboard(client, staff_user):
    """Test: Mitarbeiter können nicht auf Admin-Dashboard zugreifen"""
    client.force_login(staff_user)

    response = client.get(reverse("admin:dashboard"))

    # Sollte 403 oder Redirect sein
    assert response.status_code in [403, 302]


@pytest.mark.django_db
def test_user_list_view(client, board_user):
    """Test: Benutzer-Liste anzeigen"""
    client.force_login(board_user)

    response = client.get(reverse("admin:user_list"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_create_staff_user(client, board_user):
    """Test: Mitarbeiter-Account erstellen"""
    from apps.accounts.models import User

    client.force_login(board_user)

    response = client.post(
        reverse("admin:user_create"),
        {
            "email": "newstaff@example.com",
            "first_name": "Neuer",
            "last_name": "Mitarbeiter",
            "role": User.ROLE_STAFF,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        },
    )

    assert response.status_code == 302
    assert User.objects.filter(email="newstaff@example.com", role=User.ROLE_STAFF).exists()


@pytest.mark.django_db
def test_deactivate_user(client, board_user, member_user):
    """Test: Benutzer deaktivieren"""
    client.force_login(board_user)

    response = client.post(
        reverse("admin:user_deactivate", kwargs={"pk": member_user.pk}),
    )

    assert response.status_code == 302
    
    member_user.refresh_from_db()
    assert member_user.is_active is False


@pytest.mark.django_db
def test_system_settings_view(client, board_user):
    """Test: System-Einstellungen anzeigen"""
    client.force_login(board_user)

    response = client.get(reverse("admin:settings"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_update_club_settings(client, board_user):
    """Test: Club-Einstellungen ändern"""
    client.force_login(board_user)

    response = client.post(
        reverse("admin:settings"),
        {
            "club_name": "CSC Leipzig Süd",
            "club_email": "info@csc-leipzig.eu",
            "max_members": "500",
            "daily_limit": "25",
            "monthly_limit": "50",
        },
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_email_template_list(client, board_user):
    """Test: E-Mail-Template-Liste"""
    client.force_login(board_user)

    response = client.get(reverse("admin:email_templates"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_update_email_template(client, board_user):
    """Test: E-Mail-Template bearbeiten"""
    from apps.messaging.models import EmailTemplate

    template = EmailTemplate.objects.create(
        name="Willkommens-E-Mail",
        slug="welcome",
        subject="Willkommen!",
        body="Hallo {{ first_name }}",
    )

    client.force_login(board_user)

    response = client.post(
        reverse("admin:email_template_edit", kwargs={"pk": template.pk}),
        {
            "subject": "Herzlich willkommen!",
            "body": "Hallo {{ first_name }}, schön dass du da bist!",
        },
    )

    assert response.status_code == 302
    
    template.refresh_from_db()
    assert template.subject == "Herzlich willkommen!"


@pytest.mark.django_db
def test_meeting_schedule_create(client, board_user):
    """Test: Mitgliederversammlung planen"""
    from apps.meetings.models import Meeting

    client.force_login(board_user)

    response = client.post(
        reverse("admin:meeting_create"),
        {
            "title": "Quartals-MV Q1 2026",
            "date": date.today().isoformat(),
            "time": "19:00",
            "location": "Online (Google Meet)",
            "description": "Tagesordnung: Berichte, Wahlen",
        },
    )

    assert response.status_code == 302
    assert Meeting.objects.filter(title="Quartals-MV Q1 2026").exists()


@pytest.mark.django_db
def test_backup_trigger(client, board_user):
    """Test: Manuelles Backup auslösen"""
    client.force_login(board_user)

    response = client.post(reverse("admin:backup_trigger"))

    assert response.status_code == 302
    # Backup sollte gestartet werden


@pytest.mark.django_db
def test_audit_log_view(client, board_user):
    """Test: Audit-Log anzeigen"""
    client.force_login(board_user)

    response = client.get(reverse("admin:audit_log"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_role_permissions_view(client, board_user):
    """Test: Rollen-Berechtigungen anzeigen"""
    client.force_login(board_user)

    response = client.get(reverse("admin:role_permissions"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_update_role_permissions(client, board_user):
    """Test: Rollen-Berechtigungen ändern"""
    from django.contrib.auth.models import Permission
    from apps.accounts.models import User

    client.force_login(board_user)

    # Berechtigung zuweisen
    perm = Permission.objects.first()
    
    response = client.post(
        reverse("admin:role_permissions_update"),
        {
            "role": User.ROLE_STAFF,
            "permissions": [perm.pk],
        },
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_member_limit_warning(client, board_user):
    """Test: Warnung bei 90% Mitgliedslimit"""
    from apps.accounts.models import User
    from apps.members.models import Profile

    # Erstelle viele Mitglieder (simuliert 450/500)
    for i in range(450):
        user = User.objects.create_user(
            email=f"member{i}@example.com",
            password="pass",
            first_name=f"Member{i}",
            last_name="Test",
            role=User.ROLE_MEMBER,
        )
        Profile.objects.create(
            user=user,
            birth_date=date(1990, 1, 1),
            status=Profile.STATUS_ACTIVE,
            member_number=100000 + i,
        )

    client.force_login(board_user)

    response = client.get(reverse("admin:dashboard"))

    assert response.status_code == 200
    # Sollte Warnung anzeigen
    assert "90%" in str(response.content) or "limit" in str(response.content).lower()


@pytest.mark.django_db
def test_system_health_check(client, board_user):
    """Test: System-Health-Check"""
    client.force_login(board_user)

    response = client.get(reverse("admin:health_check"))

    assert response.status_code == 200
    # Sollte System-Status zeigen
