from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.governance.forms import BoardMeetingForm, IntegrationEndpointForm
from apps.governance.models import BoardMeeting, BoardTask, IntegrationEndpoint
from apps.members.models import Profile


@pytest.fixture
def board_user(db):
    user = User.objects.create_user(
        email="gov-board@example.com",
        password="StrongPass123!",
        first_name="Gov",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    Profile.objects.create(
        user=user,
        birth_date=timezone.datetime(1988, 1, 1).date(),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    return user


def test_board_meeting_form_combines_date_and_time():
    form = BoardMeetingForm(
        data={
            "title": "Test Meeting",
            "meeting_type": BoardMeeting.TYPE_GENERAL,
            "location": "Online",
            "participation_url": "https://example.org/meet",
            "minutes_url": "",
            "agenda_submission_email": "agenda@example.org",
            "invitation_lead_days": 3,
            "reminder_lead_hours": 12,
            "chairperson": "",
            "scheduled_date": timezone.localdate().isoformat(),
            "scheduled_time": "10:30",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["scheduled_for"] is not None


def test_integration_endpoint_form_rejects_invalid_endpoint_url():
    form = IntegrationEndpointForm(
        data={
            "name": "Bad Endpoint",
            "integration_type": IntegrationEndpoint.TYPE_EXTERNAL,
            "endpoint_url": "ftp://bad",
            "auth_header_name": "Authorization",
            "auth_token": "",
            "enabled": True,
            "subscribed_events_input": "*",
            "resource_scope_input": "members",
        }
    )
    assert form.is_valid() is False
    assert "endpoint_url" in form.errors


@pytest.mark.django_db
def test_governance_tasks_status_update(client, board_user):
    task = BoardTask.objects.create(title="Task 1", created_by=board_user)
    client.force_login(board_user)

    response = client.post(
        reverse("governance:tasks"),
        data={"action": "status", "task_id": task.id, "status": BoardTask.STATUS_DONE},
        follow=True,
    )

    task.refresh_from_db()
    assert response.status_code == 200
    assert task.status == BoardTask.STATUS_DONE


@pytest.mark.django_db
def test_governance_api_export_requires_valid_api_key(client, board_user):
    client.force_login(board_user)
    response = client.get(reverse("governance:api_export", args=["members"]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_governance_api_export_success_with_scoped_key(client, board_user):
    endpoint = IntegrationEndpoint.objects.create(
        name="Members API",
        endpoint_url="https://example.org/hook",
        resource_scope=["members"],
        subscribed_events=["*"],
        enabled=True,
    )
    client.force_login(board_user)
    response = client.get(reverse("governance:api_export", args=["members"]), {"api_key": endpoint.api_key})
    assert response.status_code == 200
    assert response.json()["resource"] == "members"
