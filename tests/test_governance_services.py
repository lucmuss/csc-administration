from __future__ import annotations

import json
from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.core.models import SocialClub
from apps.governance.models import BoardMeeting, IntegrationDelivery, IntegrationEndpoint
from apps.governance.services import (
    api_response_for_resource,
    dispatch_webhook_event,
    integration_allows_resource,
    record_audit_event,
    send_due_meeting_notifications,
)


class _FakeResponse:
    def __init__(self, status=200, body=b"ok"):
        self.status = status
        self._body = body

    def read(self, n=-1):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.django_db
def test_record_audit_event_creates_entry_and_delivery(monkeypatch, member_user):
    IntegrationEndpoint.objects.create(
        name="Webhook A",
        endpoint_url="https://example.invalid/hook",
        api_key="key-1",
        subscribed_events=["*"],
        enabled=True,
    )
    monkeypatch.setattr("apps.governance.services.urllib_request.urlopen", lambda req, timeout=5: _FakeResponse())

    entry = record_audit_event(
        actor=member_user,
        domain="finance",
        action="updated",
        summary="Eintrag aktualisiert",
        metadata={"id": 1},
    )

    assert entry.domain == "finance"
    assert IntegrationDelivery.objects.filter(event_name="finance.updated").exists()


@pytest.mark.django_db
def test_dispatch_webhook_event_respects_event_filter(monkeypatch):
    IntegrationEndpoint.objects.create(
        name="Only Members",
        endpoint_url="https://example.invalid/members",
        api_key="k-2",
        subscribed_events=["members.updated"],
        enabled=True,
    )
    called = {"count": 0}

    def _fake_open(req, timeout=5):
        called["count"] += 1
        return _FakeResponse()

    monkeypatch.setattr("apps.governance.services.urllib_request.urlopen", _fake_open)

    dispatch_webhook_event(event_name="finance.updated", payload={"ok": True})
    assert called["count"] == 0

    dispatch_webhook_event(event_name="members.updated", payload={"ok": True})
    assert called["count"] == 1


@pytest.mark.django_db
def test_integration_allows_resource_scope():
    endpoint = IntegrationEndpoint.objects.create(
        name="Scoped",
        endpoint_url="https://example.invalid/scope",
        api_key="scope-key",
        resource_scope=["members"],
        enabled=True,
    )

    assert integration_allows_resource("scope-key", "members") is not None
    assert integration_allows_resource("scope-key", "invoices") is None


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_send_due_meeting_notifications_sends_invitation_and_reminder(member_user):
    now = timezone.now()
    meeting = BoardMeeting.objects.create(
        title="Generalversammlung",
        meeting_type=BoardMeeting.TYPE_GENERAL,
        status=BoardMeeting.STATUS_PLANNED,
        scheduled_for=now,
        invitation_lead_days=0,
        reminder_lead_hours=0,
    )

    result = send_due_meeting_notifications(now=now)

    assert result["invitations"] >= 1
    assert result["reminders"] >= 1
    meeting.refresh_from_db()
    assert meeting.invitation_sent_at is not None
    assert meeting.reminder_sent_at is not None


@pytest.mark.django_db
def test_api_response_for_supported_resource(member_user):
    payload = api_response_for_resource("members")
    assert payload["resource"] == "members"
    assert isinstance(payload["items"], list)
