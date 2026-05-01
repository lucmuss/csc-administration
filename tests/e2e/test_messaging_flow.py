"""E2E Tests: Messaging Flow (Massen-E-Mails)

Testet: E-Mail-Gruppen, Massen-E-Mails, Tracking
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_create_email_group(client, board_user):
    """Test: E-Mail-Gruppe erstellen"""
    from apps.messaging.models import EmailGroup

    client.force_login(board_user)

    response = client.post(
        reverse("messaging:email_group_create"),
        {
            "name": "Test Gruppe",
            "description": "Eine Test-Beschreibung",
        },
    )

    assert response.status_code == 302  # Redirect nach Erfolg
    assert EmailGroup.objects.filter(name="Test Gruppe").exists()


@pytest.mark.django_db
def test_create_email_group_duplicate_name(client, board_user, email_group):
    """Test: E-Mail-Gruppe mit doppeltem Namen abgelehnt"""
    client.force_login(board_user)

    response = client.post(
        reverse("messaging:email_group_create"),
        {
            "name": email_group.name,  # Bereits existiert
            "description": "Andere Beschreibung",
        },
    )

    # Sollte Fehler zeigen
    assert response.status_code == 200


@pytest.mark.django_db
def test_add_member_to_group(client, board_user, email_group, pending_member):
    """Test: Mitglieder zu Gruppe hinzufügen"""
    from apps.messaging.models import EmailGroupMember

    client.force_login(board_user)

    response = client.post(
        reverse("messaging:email_group_add_members", kwargs={"pk": email_group.pk}),
        {
            "members": [pending_member.profile.pk],
        },
    )

    assert response.status_code == 302
    assert EmailGroupMember.objects.filter(group=email_group, member=pending_member.profile).exists()


@pytest.mark.django_db
def test_remove_member_from_group(client, board_user, email_group, member_user):
    """Test: Mitglieder aus Gruppe entfernen"""
    from apps.messaging.models import EmailGroupMember

    EmailGroupMember.objects.get_or_create(group=email_group, member=member_user.profile)
    
    client.force_login(board_user)

    response = client.post(
        reverse("messaging:email_group_remove_member", kwargs={
            "pk": email_group.pk,
            "member_pk": member_user.profile.pk
        }),
    )

    assert response.status_code == 302
    assert not EmailGroupMember.objects.filter(group=email_group, member=member_user.profile).exists()


@pytest.mark.django_db
def test_mass_email_create_draft(client, board_user):
    """Test: Massen-E-Mail erstellen (Draft)"""
    from apps.messaging.models import MassEmail

    client.force_login(board_user)

    response = client.post(
        reverse("messaging:mass_email_create"),
        {
            "subject": "Test E-Mail",
            "content": "Hallo {{ first_name }}!",
            "recipient_type": MassEmail.RECIPIENT_ALL,
        },
    )

    assert response.status_code == 302
    
    email = MassEmail.objects.first()
    assert email is not None
    assert email.subject == "Test E-Mail"
    assert email.content == "Hallo {{ first_name }}!"
    assert email.status == MassEmail.STATUS_DRAFT


@pytest.mark.django_db
def test_mass_email_preview(client, board_user, mass_email_draft):
    """Test: E-Mail-Vorschau anzeigen"""
    client.force_login(board_user)

    response = client.get(
        reverse("messaging:mass_email_preview", kwargs={"pk": mass_email_draft.pk})
    )

    assert response.status_code == 200
    assert mass_email_draft.subject in str(response.content)


@pytest.mark.django_db
def test_mass_email_send(client, board_user, mass_email_draft, member_user):
    """Test: E-Mail senden (wird gequeued)"""
    from apps.messaging.models import MassEmail

    client.force_login(board_user)

    response = client.post(
        reverse("messaging:mass_email_send", kwargs={"pk": mass_email_draft.pk}),
    )

    assert response.status_code == 302
    
    mass_email_draft.refresh_from_db()
    assert mass_email_draft.status in [MassEmail.STATUS_QUEUED, MassEmail.STATUS_SENT]


@pytest.mark.django_db
def test_mass_email_send_to_group(client, board_user, email_group):
    """Test: E-Mail an spezifische Gruppe senden"""
    from apps.messaging.models import MassEmail

    client.force_login(board_user)

    response = client.post(
        reverse("messaging:mass_email_create"),
        {
            "subject": "Gruppen-E-Mail",
            "content": "Hallo Gruppe!",
            "recipient_type": MassEmail.RECIPIENT_GROUP,
            "recipient_group": email_group.pk,
        },
    )

    assert response.status_code == 302
    
    email = MassEmail.objects.first()
    assert email.recipient_type == MassEmail.RECIPIENT_GROUP
    assert email.recipient_group == email_group


@pytest.mark.django_db
def test_mass_email_send_to_individuals(client, board_user, member_user, pending_member):
    """Test: E-Mail an individuelle Empfänger senden"""
    from apps.messaging.models import MassEmail

    client.force_login(board_user)

    response = client.post(
        reverse("messaging:mass_email_create"),
        {
            "subject": "Individuelle E-Mail",
            "content": "Hallo!",
            "recipient_type": MassEmail.RECIPIENT_INDIVIDUAL,
            "recipient_individuals": [member_user.pk, pending_member.pk],
        },
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_email_tracking_logs_created(client, board_user, mass_email_draft, member_user):
    """Test: Tracking-Logs werden erstellt"""
    from apps.messaging.models import EmailLog

    client.force_login(board_user)

    # E-Mail senden
    client.post(
        reverse("messaging:mass_email_send", kwargs={"pk": mass_email_draft.pk}),
    )

    # Logs sollten existieren
    logs = EmailLog.objects.filter(mass_email=mass_email_draft)
    assert logs.exists()


@pytest.mark.django_db
def test_email_group_list_view(client, board_user, email_group):
    """Test: E-Mail-Gruppen-Liste anzeigen"""
    client.force_login(board_user)

    response = client.get(reverse("messaging:email_group_list"))

    assert response.status_code == 200
    assert email_group.name in str(response.content)


@pytest.mark.django_db
def test_mass_email_list_view(client, board_user, mass_email_draft):
    """Test: Massen-E-Mail-Liste anzeigen"""
    client.force_login(board_user)

    response = client.get(reverse("messaging:mass_email_list"))

    assert response.status_code == 200
    assert mass_email_draft.subject in str(response.content)


@pytest.mark.django_db
def test_delete_email_group(client, board_user, email_group):
    """Test: E-Mail-Gruppe löschen"""
    from apps.messaging.models import EmailGroup

    client.force_login(board_user)

    response = client.post(
        reverse("messaging:email_group_delete", kwargs={"pk": email_group.pk}),
    )

    assert response.status_code == 302
    assert not EmailGroup.objects.filter(pk=email_group.pk).exists()


@pytest.mark.django_db
def test_delete_mass_email(client, board_user, mass_email_draft):
    """Test: Massen-E-Mail löschen"""
    from apps.messaging.models import MassEmail

    client.force_login(board_user)

    response = client.post(
        reverse("messaging:mass_email_delete", kwargs={"pk": mass_email_draft.pk}),
    )

    assert response.status_code == 302
    assert not MassEmail.objects.filter(pk=mass_email_draft.pk).exists()


@pytest.mark.django_db
def test_messaging_requires_staff(client, member_user):
    """Test: Messaging nur für Staff/Vorstand"""
    client.force_login(member_user)

    response = client.get(reverse("messaging:email_group_list"))
    
    # Sollte 403 oder Redirect sein
    assert response.status_code in [403, 302]
