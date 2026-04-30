from __future__ import annotations

from datetime import date
from decimal import Decimal
import importlib
import sys
import types

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.members.models import Profile
from apps.messaging.models import EmailGroupMember, SmsCostLog, SmsMessage, SmsProviderConfig
from apps.messaging.services import (
    MARKETING_EMAIL_GROUP,
    IMPORTANT_EMAIL_GROUP,
    normalize_phone_number,
    send_sms_message,
    sync_member_messaging_preferences,
)


def _load_tasks_module(monkeypatch):
    fake_celery = types.ModuleType("celery")
    fake_celery.shared_task = lambda fn: fn
    monkeypatch.setitem(sys.modules, "celery", fake_celery)
    return importlib.import_module("apps.messaging.tasks")


@pytest.mark.django_db
def test_sync_member_messaging_preferences_assigns_and_removes_groups(member_user):
    profile = member_user.profile
    profile.optional_newsletter_opt_in = True
    profile.status = Profile.STATUS_ACTIVE
    profile.is_verified = True
    profile.save(update_fields=["optional_newsletter_opt_in", "status", "is_verified", "updated_at"])

    sync_member_messaging_preferences(profile)
    assert EmailGroupMember.objects.filter(member=profile, group__name=IMPORTANT_EMAIL_GROUP).exists()
    assert EmailGroupMember.objects.filter(member=profile, group__name=MARKETING_EMAIL_GROUP).exists()

    profile.optional_newsletter_opt_in = False
    profile.save(update_fields=["optional_newsletter_opt_in", "updated_at"])
    sync_member_messaging_preferences(profile)
    assert not EmailGroupMember.objects.filter(member=profile, group__name=MARKETING_EMAIL_GROUP).exists()


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("0176 1234567", "+491761234567"),
        ("00491761234567", "+491761234567"),
        ("+491761234567", "+491761234567"),
    ],
)
def test_normalize_phone_number(raw, expected):
    assert normalize_phone_number(raw) == expected


@pytest.mark.django_db
def test_send_sms_message_fails_without_provider(member_user):
    sms = SmsMessage.objects.create(
        recipient_member=member_user.profile,
        recipient_phone="+491761234567",
        content="Test",
        status="queued",
    )
    ok = send_sms_message(sms)
    sms.refresh_from_db()
    assert ok is False
    assert sms.status == "failed"


@pytest.mark.django_db
def test_send_sms_message_success_with_mocked_provider(member_user, monkeypatch):
    provider = SmsProviderConfig.objects.create(
        provider="custom",
        name="Mock",
        api_key="k",
        api_secret="s",
        sender_number="CSC",
        webhook_url="https://example.invalid",
        is_active=True,
        cost_per_sms=Decimal("0.0500"),
    )
    sms = SmsMessage.objects.create(
        recipient_member=member_user.profile,
        recipient_phone="+491761234567",
        content="Hallo Welt",
        status="queued",
        provider=provider,
    )

    monkeypatch.setattr(
        "apps.messaging.services.get_sms_service",
        lambda _provider: type("MockSvc", (), {"send_sms": staticmethod(lambda to, message: {"success": True, "external_id": "ext-1"})})(),
    )

    ok = send_sms_message(sms)
    sms.refresh_from_db()
    assert ok is True
    assert sms.status == "sent"
    assert sms.external_id == "ext-1"


@pytest.mark.django_db
def test_send_sms_task_handles_missing_sms_with_stubbed_celery(monkeypatch):
    tasks = _load_tasks_module(monkeypatch)
    result = tasks.send_sms_task("00000000-0000-0000-0000-000000000000")
    assert "error" in result


@pytest.mark.django_db
def test_send_sms_task_updates_status_via_service(member_user, monkeypatch):
    tasks = _load_tasks_module(monkeypatch)
    provider = SmsProviderConfig.objects.create(
        provider="custom",
        name="Task Provider",
        api_key="k",
        api_secret="s",
        sender_number="CSC",
        webhook_url="https://example.invalid",
        is_active=True,
    )
    sms = SmsMessage.objects.create(
        recipient_member=member_user.profile,
        recipient_phone="+491761234567",
        content="Task SMS",
        status="queued",
        provider=provider,
    )
    monkeypatch.setattr(tasks, "send_sms_message", lambda message: True)

    result = tasks.send_sms_task(str(sms.id))
    sms.refresh_from_db()
    assert result["success"] is True


@pytest.mark.django_db
def test_update_sms_cost_log_aggregates_current_month_with_stubbed_celery(member_user, monkeypatch):
    tasks = _load_tasks_module(monkeypatch)
    provider = SmsProviderConfig.objects.create(
        provider="custom",
        name="Cost Provider",
        api_key="k",
        api_secret="s",
        sender_number="CSC",
        webhook_url="https://example.invalid",
        is_active=True,
    )
    SmsMessage.objects.create(
        recipient_member=member_user.profile,
        recipient_phone="+491761234567",
        content="A",
        status="sent",
        provider=provider,
        cost=Decimal("0.0500"),
        sent_at=timezone.now(),
    )
    SmsMessage.objects.create(
        recipient_member=member_user.profile,
        recipient_phone="+491761234568",
        content="B",
        status="sent",
        provider=provider,
        cost=Decimal("0.0700"),
        sent_at=timezone.now(),
    )

    result = tasks.update_sms_cost_log()
    month = timezone.now().strftime("%Y-%m")
    log = SmsCostLog.objects.get(month=month)

    assert result["total_messages"] >= 2
    assert log.total_messages >= 2
    assert float(log.total_cost) >= 0.12
