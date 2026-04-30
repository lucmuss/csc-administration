from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.emails import send_verification_reminder_email
from apps.accounts.models import User
from apps.members.models import Profile


class Command(BaseCommand):
    help = "Sendet alle 14 Tage Erinnerungen an nicht verifizierte Mitglieder."

    def handle(self, *args, **options):
        now = timezone.now()
        threshold = now - timedelta(days=14)
        candidates = (
            Profile.objects.select_related("user")
            .filter(user__role=User.ROLE_MEMBER)
            .filter(is_verified=False)
            .filter(registration_completed_at__isnull=False)
            .filter(status__in=[Profile.STATUS_PENDING, Profile.STATUS_VERIFIED])
        )
        sent = 0
        for profile in candidates:
            if profile.verification_reminder_sent_at and profile.verification_reminder_sent_at > threshold:
                continue
            if send_verification_reminder_email(profile.user, profile):
                profile.verification_reminder_sent_at = now
                profile.save(update_fields=["verification_reminder_sent_at", "updated_at"])
                sent += 1
        self.stdout.write(self.style.SUCCESS(f"Verifizierungs-Erinnerungen versendet: {sent}"))
