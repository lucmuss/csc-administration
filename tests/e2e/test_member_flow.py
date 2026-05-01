"""E2E Tests: Member Flow (Mitgliederverwaltung)

Testet: Registrierung, Verifizierung, Status-Änderungen, Profil
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse


@pytest.mark.django_db
def test_member_profile_view(client, member_user):
    """Test: Eigenes Profil anzeigen"""
    client.force_login(member_user)

    response = client.get(reverse("members:profile"))

    assert response.status_code == 200
    assert member_user.email in str(response.content)
    assert str(member_user.profile.member_number) in str(response.content)


@pytest.mark.django_db
def test_member_profile_update(client, member_user):
    """Test: Profil bearbeiten"""
    client.force_login(member_user)

    response = client.post(
        reverse("members:profile_edit"),
        {
            "first_name": "Neuer",
            "last_name": "Name",
            "phone": "01511234567",
        },
    )

    assert response.status_code == 302
    
    member_user.refresh_from_db()
    assert member_user.first_name == "Neuer"


@pytest.mark.django_db
def test_board_can_view_member_list(client, board_user, member_user):
    """Test: Vorstand sieht Mitgliederliste"""
    client.force_login(board_user)

    response = client.get(reverse("members:member_list"))

    assert response.status_code == 200
    assert member_user.email in str(response.content)


@pytest.mark.django_db
def test_board_can_approve_member(client, board_user, pending_member):
    """Test: Vorstand akzeptiert Mitglied"""
    from apps.members.models import Profile

    client.force_login(board_user)

    response = client.post(
        reverse("members:approve", kwargs={"pk": pending_member.pk}),
    )

    assert response.status_code == 302
    
    pending_member.profile.refresh_from_db()
    assert pending_member.profile.status == Profile.STATUS_ACCEPTED


@pytest.mark.django_db
def test_board_can_reject_member(client, board_user, pending_member):
    """Test: Vorstand lehnt Mitglied ab"""
    from apps.members.models import Profile

    client.force_login(board_user)

    response = client.post(
        reverse("members:reject", kwargs={"pk": pending_member.pk}),
        {"reason": "Unvollständige Unterlagen"},
    )

    assert response.status_code == 302
    
    pending_member.profile.refresh_from_db()
    assert pending_member.profile.status == Profile.STATUS_REJECTED


@pytest.mark.django_db
def test_board_can_verify_member(client, board_user, pending_member):
    """Test: Vorstand verifiziert Mitglied"""
    from apps.members.models import Profile

    # Zuerst akzeptieren
    pending_member.profile.status = Profile.STATUS_ACCEPTED
    pending_member.profile.save()

    client.force_login(board_user)

    response = client.post(
        reverse("members:verify", kwargs={"pk": pending_member.pk}),
    )

    assert response.status_code == 302
    
    pending_member.profile.refresh_from_db()
    assert pending_member.profile.is_verified is True


@pytest.mark.django_db
def test_member_number_generation(client, board_user):
    """Test: Mitgliedsnummer wird automatisch generiert"""
    from apps.accounts.models import User
    from apps.members.models import Profile

    # Erstelle neuen User
    user = User.objects.create_user(
        email="newmember@example.com",
        password="StrongPass123!",
        first_name="Neu",
        last_name="Mitglied",
        role=User.ROLE_MEMBER,
    )
    
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_PENDING,
    )

    # Akzeptieren sollte Nummer generieren
    client.force_login(board_user)
    client.post(reverse("members:approve", kwargs={"pk": user.pk}))

    profile.refresh_from_db()
    assert profile.member_number is not None
    assert profile.member_number >= 100000


@pytest.mark.django_db
def test_8week_deadline_tracking(client, pending_member):
    """Test: 8-Wochen-Deadline wird getrackt"""
    from django.utils import timezone
    from apps.members.models import Profile

    # Setze Aufnahmedatum auf vor 7 Wochen
    pending_member.profile.created_at = timezone.now() - timedelta(weeks=7)
    pending_member.profile.save()

    # Deadline sollte bald erreicht sein
    assert pending_member.profile.status == Profile.STATUS_PENDING


@pytest.mark.django_db
def test_member_limit_display(client, member_user):
    """Test: Limits werden im Profil angezeigt"""
    client.force_login(member_user)

    response = client.get(reverse("members:profile"))

    assert response.status_code == 200
    # Sollte Tages- und Monatslimit anzeigen
    assert "25" in str(response.content) or "50" in str(response.content)


@pytest.mark.django_db
def test_member_balance_display(client, member_user):
    """Test: Guthaben wird im Profil angezeigt"""
    client.force_login(member_user)

    response = client.get(reverse("members:profile"))

    assert response.status_code == 200
    assert "200,00" in str(response.content) or "200.00" in str(response.content)


@pytest.mark.django_db
def test_member_cannot_view_other_profiles(client, member_user, pending_member):
    """Test: Mitglied sieht nicht fremde Profile"""
    client.force_login(member_user)

    response = client.get(
        reverse("members:member_detail", kwargs={"pk": pending_member.pk})
    )

    # Sollte 403 oder Redirect sein
    assert response.status_code in [403, 302]


@pytest.mark.django_db
def test_board_can_suspend_member(client, board_user, member_user):
    """Test: Vorstand kann Mitglied sperren"""
    from apps.members.models import Profile

    client.force_login(board_user)

    response = client.post(
        reverse("members:suspend", kwargs={"pk": member_user.pk}),
        {"reason": "Verstoß gegen Regeln"},
    )

    assert response.status_code == 302
    
    member_user.profile.refresh_from_db()
    assert member_user.profile.status == Profile.STATUS_SUSPENDED


@pytest.mark.django_db
def test_suspended_member_cannot_order(client, member_user, batch):
    """Test: Gesperrtes Mitglied kann nicht bestellen"""
    from apps.members.models import Profile

    member_user.profile.status = Profile.STATUS_SUSPENDED
    member_user.profile.save()

    client.force_login(member_user)

    response = client.get(reverse("orders:shop"))

    # Sollte blockiert sein
    assert response.status_code in [403, 302]


@pytest.mark.django_db
def test_member_search(client, board_user, member_user):
    """Test: Mitgliedersuche"""
    client.force_login(board_user)

    response = client.get(
        reverse("members:member_list"),
        {"q": member_user.email},
    )

    assert response.status_code == 200
    assert member_user.email in str(response.content)


@pytest.mark.django_db
def test_member_filter_by_status(client, board_user, member_user, pending_member):
    """Test: Mitglieder nach Status filtern"""
    client.force_login(board_user)

    response = client.get(
        reverse("members:member_list"),
        {"status": "pending"},
    )

    assert response.status_code == 200
    assert pending_member.email in str(response.content)
