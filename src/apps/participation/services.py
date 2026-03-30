from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Max, Sum
from django.template.loader import render_to_string
from django.utils import timezone

from apps.compliance.services import reset_daily_limits, reset_monthly_limits
from apps.members.models import Profile
from apps.orders.models import Order

from .models import MemberEngagement


class LimitResetService:
    @staticmethod
    def reset_daily(target_date: date | None = None) -> int:
        return reset_daily_limits(target_date=target_date)

    @staticmethod
    def reset_monthly(target_date: date | None = None) -> int:
        return reset_monthly_limits(target_date=target_date)


class MeetingService:
    @staticmethod
    def _engagements_with_meeting(target_date: date):
        return MemberEngagement.objects.select_related("profile__user").filter(annual_meeting_date=target_date)

    @staticmethod
    def send_invitations(today: date | None = None) -> int:
        today = today or timezone.localdate()
        meeting_day = today + timedelta(days=14)
        sent = 0

        for engagement in MeetingService._engagements_with_meeting(meeting_day):
            if engagement.invitation_sent_at:
                continue
            body = render_to_string(
                "emails/meeting_invitation.html",
                {
                    "profile": engagement.profile,
                    "meeting_date": engagement.annual_meeting_date,
                },
            )
            send_mail(
                subject="Einladung zur Mitgliederversammlung",
                message="Bitte HTML-Version anzeigen.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[engagement.profile.user.email],
                html_message=body,
                fail_silently=True,
            )
            engagement.invitation_sent_at = timezone.now()
            engagement.save(update_fields=["invitation_sent_at", "updated_at"])
            sent += 1

        return sent

    @staticmethod
    def send_reminders(today: date | None = None) -> int:
        today = today or timezone.localdate()
        meeting_day = today + timedelta(days=2)
        sent = 0

        for engagement in MeetingService._engagements_with_meeting(meeting_day):
            if engagement.reminder_sent_at:
                continue
            body = render_to_string(
                "emails/meeting_reminder.html",
                {
                    "profile": engagement.profile,
                    "meeting_date": engagement.annual_meeting_date,
                },
            )
            send_mail(
                subject="Erinnerung: Mitgliederversammlung",
                message="Bitte HTML-Version anzeigen.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[engagement.profile.user.email],
                html_message=body,
                fail_silently=True,
            )
            engagement.reminder_sent_at = timezone.now()
            engagement.save(update_fields=["reminder_sent_at", "updated_at"])
            sent += 1

        return sent


class InactivityService:
    INACTIVITY_DAYS = 60

    @staticmethod
    def _inactive_profiles(today: date):
        cutoff = timezone.now() - timedelta(days=InactivityService.INACTIVITY_DAYS)
        profiles = Profile.objects.select_related("user").all()

        inactive_ids = []
        for profile in profiles:
            last_order = (
                Order.objects.filter(member=profile.user)
                .exclude(status=Order.STATUS_CANCELLED)
                .aggregate(last=Max("created_at"))["last"]
            )
            last_activity = profile.last_activity or last_order
            if not last_activity or last_activity <= cutoff:
                inactive_ids.append(profile.id)

        return Profile.objects.filter(id__in=inactive_ids).select_related("user")

    @staticmethod
    def notify_inactive_members(today: date | None = None) -> int:
        today = today or timezone.localdate()
        sent = 0

        for profile in InactivityService._inactive_profiles(today=today):
            engagement, _ = MemberEngagement.objects.get_or_create(profile=profile)
            if engagement.inactivity_notified_at and engagement.inactivity_notified_at.date() >= today:
                continue

            body = render_to_string("emails/inactivity_reminder.html", {"profile": profile})
            send_mail(
                subject="Wir haben Sie laenger nicht gesehen",
                message="Bitte HTML-Version anzeigen.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[profile.user.email],
                html_message=body,
                fail_silently=True,
            )
            engagement.inactivity_notified_at = timezone.now()
            engagement.save(update_fields=["inactivity_notified_at", "updated_at"])
            sent += 1

        return sent


class DeadlineService:
    @staticmethod
    def check_8week_deadline(today: date | None = None) -> int:
        today = today or timezone.localdate()
        sent = 0

        due_engagements = MemberEngagement.objects.select_related("profile__user").filter(
            registration_completed=False,
            registration_deadline__isnull=False,
            registration_deadline__lte=today,
        )

        for engagement in due_engagements:
            if engagement.registration_reminder_sent_at:
                continue

            send_mail(
                subject="Erinnerung: 8-Wochen-Registrierung",
                message=(
                    f"Die Registrierung ist noch offen. Frist: {engagement.registration_deadline:%d.%m.%Y}."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[engagement.profile.user.email],
                fail_silently=True,
            )
            engagement.registration_reminder_sent_at = timezone.now()
            engagement.save(update_fields=["registration_reminder_sent_at", "updated_at"])
            sent += 1

        return sent


def sync_profile_work_hours(profile: Profile) -> Decimal:
    total = profile.work_hours.filter(approved=True).aggregate(total=Sum("hours"))["total"] or Decimal("0.00")
    profile.work_hours_done = total
    profile.save(update_fields=["work_hours_done", "updated_at"])
    return total
