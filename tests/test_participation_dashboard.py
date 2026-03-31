from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_member_can_submit_work_hours_entry(client, member_user):
    client.force_login(member_user)

    response = client.post(
        reverse("participation:dashboard"),
        data={
            "date": date.today().isoformat(),
            "hours": "2.5",
            "notes": "Aufbau vor der Ausgabe geholfen",
            "shift": "",
        },
    )

    entry = member_user.profile.work_hours.get()
    assert response.status_code == 302
    assert entry.approved is False
    assert entry.hours == Decimal("2.50")


@pytest.mark.django_db
def test_admin_can_approve_work_hours_entry(client, member_user):
    from apps.accounts.models import User
    from apps.members.models import Profile
    from apps.participation.models import WorkHours

    board = User.objects.create_user(
        email="board-hours@example.com",
        password="StrongPass123!",
        first_name="Bea",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    Profile.objects.create(
        user=board,
        birth_date=date(1988, 5, 5),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100010,
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    entry = WorkHours.objects.create(
        profile=member_user.profile,
        date=date.today(),
        hours=Decimal("3.00"),
        notes="Schicht vorbereitet",
        approved=False,
    )

    client.force_login(board)
    response = client.post(
        reverse("participation:admin_hours"),
        data={"entry_id": entry.id, "action": "approve"},
    )

    entry.refresh_from_db()
    member_user.profile.refresh_from_db()
    assert response.status_code == 302
    assert entry.approved is True
    assert member_user.profile.work_hours_done == Decimal("3.00")
