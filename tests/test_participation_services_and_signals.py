from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.members.models import Profile
from apps.participation.models import MemberEngagement, WorkHours
from apps.participation.services import DeadlineService, InactivityService, MeetingService, sync_profile_work_hours


@pytest.fixture
def unverified_member(db):
    user = User.objects.create_user(
        email="unverified-part@example.com",
        password="StrongPass123!",
        first_name="Un",
        last_name="Verified",
        role=User.ROLE_MEMBER,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1995, 5, 5),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    return user


@pytest.mark.django_db
@override_settings(ENFORCE_ONBOARDING_REDIRECT_IN_TESTS=True)
def test_participation_dashboard_blocks_unverified_member(client, unverified_member):
    client.force_login(unverified_member)
    response = client.get(reverse("participation:dashboard"))
    assert response.status_code == 302
    assert response.url == reverse("members:onboarding")


@pytest.mark.django_db
def test_sync_profile_work_hours_updates_approved_sum(member_user):
    WorkHours.objects.create(profile=member_user.profile, date=date.today(), hours=Decimal("2.50"), approved=True)
    WorkHours.objects.create(profile=member_user.profile, date=date.today(), hours=Decimal("1.00"), approved=False)

    total = sync_profile_work_hours(member_user.profile)
    member_user.profile.refresh_from_db()

    assert total == Decimal("2.50")
    assert member_user.profile.work_hours_done == Decimal("2.50")


@pytest.mark.django_db
def test_workhours_delete_signal_recalculates_profile_hours(member_user):
    e1 = WorkHours.objects.create(profile=member_user.profile, date=date.today(), hours=Decimal("2.00"), approved=True)
    e2 = WorkHours.objects.create(profile=member_user.profile, date=date.today(), hours=Decimal("1.50"), approved=True)
    member_user.profile.refresh_from_db()
    assert member_user.profile.work_hours_done == Decimal("3.50")

    e2.delete()
    member_user.profile.refresh_from_db()
    assert member_user.profile.work_hours_done == Decimal("2.00")


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_meeting_service_invitation_and_reminder_are_idempotent(member_user):
    today = timezone.localdate()
    engagement, _ = MemberEngagement.objects.get_or_create(profile=member_user.profile)
    engagement.annual_meeting_date = today + timedelta(days=14)
    engagement.save(update_fields=["annual_meeting_date", "updated_at"])

    first = MeetingService.send_invitations(today=today)
    second = MeetingService.send_invitations(today=today)

    assert first == 1
    assert second == 0

    engagement.annual_meeting_date = today + timedelta(days=2)
    engagement.reminder_sent_at = None
    engagement.save(update_fields=["annual_meeting_date", "reminder_sent_at", "updated_at"])

    r_first = MeetingService.send_reminders(today=today)
    r_second = MeetingService.send_reminders(today=today)

    assert r_first == 1
    assert r_second == 0
    assert len(mail.outbox) >= 2


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_deadline_service_sends_once_for_overdue_registration(member_user):
    engagement, _ = MemberEngagement.objects.get_or_create(profile=member_user.profile)
    engagement.registration_completed = False
    engagement.registration_deadline = timezone.localdate() - timedelta(days=1)
    engagement.registration_reminder_sent_at = None
    engagement.save(
        update_fields=[
            "registration_completed",
            "registration_deadline",
            "registration_reminder_sent_at",
            "updated_at",
        ]
    )

    sent1 = DeadlineService.check_8week_deadline(today=timezone.localdate())
    sent2 = DeadlineService.check_8week_deadline(today=timezone.localdate())

    assert sent1 == 1
    assert sent2 == 0


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_inactivity_service_marks_notified_and_is_idempotent(member_user):
    member_user.profile.last_activity = None
    member_user.profile.save(update_fields=["last_activity", "updated_at"])

    sent1 = InactivityService.notify_inactive_members(today=timezone.localdate())
    sent2 = InactivityService.notify_inactive_members(today=timezone.localdate())

    assert sent1 >= 1
    assert sent2 == 0
