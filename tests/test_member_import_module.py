from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.models import User
from apps.members.models import Profile


@pytest.mark.django_db
def test_csv_import_creates_members_as_pending_and_shows_result_list(client):
    board = User.objects.create_user(
        email="board-import@example.com",
        password="StrongPass123!",
        first_name="Board",
        last_name="Import",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    Profile.objects.create(
        user=board,
        birth_date=date(1988, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key="2026-04",
    )
    client.force_login(board)

    csv_content = (
        "Zeitstempel,E-Mail-Adresse,Vorname,Nachname,Geburtsdatum,Akzeptiert,Verifiziert\n"
        "07.02.2025 00:13:31,alice@example.com,Alice,Tester,03.04.1990,Ja,Ja\n"
        "07.02.2025 00:14:31,bob@example.com,Bob,Tester,04.04.1991,Ja,Nein\n"
    )
    analyze_response = client.post(
        reverse("members:import"),
        data={
            "action": "analyze",
            "csv_file": SimpleUploadedFile("members.csv", csv_content.encode("utf-8"), content_type="text/csv"),
        },
        follow=True,
    )
    assert analyze_response.status_code == 200

    import_response = client.post(
        reverse("members:import"),
        data={
            "action": "import",
            "mapping_0": "",
            "mapping_1": "email",
            "mapping_2": "first_name",
            "mapping_3": "last_name",
            "mapping_4": "birth_date",
            "mapping_5": "accepted",
            "mapping_6": "verified",
        },
        follow=True,
    )
    assert import_response.status_code == 200

    alice = User.objects.get(email="alice@example.com")
    bob = User.objects.get(email="bob@example.com")
    alice_profile = alice.profile
    bob_profile = bob.profile

    assert alice_profile.status == Profile.STATUS_PENDING
    assert bob_profile.status == Profile.STATUS_PENDING
    assert alice_profile.is_verified is False
    assert bob_profile.is_verified is False

    html = import_response.content.decode("utf-8")
    assert "Importierte Benutzer" in html
    assert "alice@example.com" in html
    assert "bob@example.com" in html
