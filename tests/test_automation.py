from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.core.management import call_command
from django.test.utils import override_settings
from django.utils import timezone


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_limit_reset_service_and_command(member_user):
    from apps.members.models import Profile

    profile = Profile.objects.get(user=member_user)
    profile.daily_used = Decimal("12.00")
    profile.monthly_used = Decimal("30.00")
    profile.daily_counter_date = timezone.localdate() - timedelta(days=1)
    profile.monthly_counter_key = "2000-01"
    profile.save(
        update_fields=["daily_used", "monthly_used", "daily_counter_date", "monthly_counter_key", "updated_at"]
    )

    call_command("reset_daily_limits")
    call_command("reset_monthly_limits")

    profile.refresh_from_db()
    assert profile.daily_used == Decimal("0.00")
    assert profile.monthly_used == Decimal("0.00")
    assert profile.daily_counter_date == timezone.localdate()
    assert profile.monthly_counter_key == timezone.localdate().strftime("%Y-%m")


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_send_meeting_invitations_and_reminders_commands(member_user):
    from apps.members.models import Profile
    from apps.participation.models import MemberEngagement
    from apps.participation.services import MeetingService

    profile = Profile.objects.get(user=member_user)
    engagement = MemberEngagement.objects.get(profile=profile)

    engagement.annual_meeting_date = timezone.localdate() + timedelta(days=14)
    engagement.save(update_fields=["annual_meeting_date", "updated_at"])

    sent = MeetingService.send_invitations()
    assert sent == 1

    engagement.refresh_from_db()
    assert engagement.invitation_sent_at is not None
    assert len(mail.outbox) == 1
    assert "Einladung" in mail.outbox[0].subject

    engagement.reminder_sent_at = None
    engagement.invitation_sent_at = None
    engagement.annual_meeting_date = timezone.localdate() + timedelta(days=2)
    engagement.save(
        update_fields=["annual_meeting_date", "invitation_sent_at", "reminder_sent_at", "updated_at"]
    )

    call_command("send_meeting_reminders")
    engagement.refresh_from_db()
    assert engagement.reminder_sent_at is not None
    assert len(mail.outbox) == 2
    assert "Erinnerung" in mail.outbox[-1].subject


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_inactivity_and_deadline_notifications(member_user):
    from apps.accounts.models import User
    from apps.members.models import Profile
    from apps.participation.models import MemberEngagement

    inactive_user = User.objects.create_user(
        email="inactive@example.com",
        password="StrongPass123!",
        first_name="In",
        last_name="Active",
        role=User.ROLE_MEMBER,
    )
    inactive_profile = Profile.objects.create(
        user=inactive_user,
        birth_date=date(1991, 2, 2),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100001,
        balance=Decimal("20.00"),
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
        last_activity=timezone.now() - timedelta(days=61),
    )
    MemberEngagement.objects.create(
        profile=inactive_profile,
        registration_deadline=timezone.localdate(),  # Deadline reached today
        registration_completed=False,
    )

    call_command("notify_inactive_members")
    call_command("check_8week_deadline")

    inactive_engagement = MemberEngagement.objects.get(profile=inactive_profile)
    assert inactive_engagement.inactivity_notified_at is not None
    assert inactive_engagement.registration_reminder_sent_at is not None
    assert len(mail.outbox) == 3  # 2 inactivity + 1 deadline
