from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.emails import send_social_club_registration_reminder_email
from apps.core.models import SocialClub


class Command(BaseCommand):
    help = "Sendet Erinnerungen fuer offene Social-Club-Registrierungen (z. B. nach 7 und 14 Tagen)."

    def handle(self, *args, **options):
        now = timezone.now()
        reminder_days = sorted(set(getattr(settings, "CLUB_REGISTRATION_REMINDER_DAYS", (7, 14))))
        if not reminder_days:
            self.stdout.write(self.style.WARNING("Keine Reminder-Tage konfiguriert."))
            return

        pending_clubs = SocialClub.objects.filter(is_approved=False, is_active=True)
        sent_count = 0
        for club in pending_clubs:
            age_days = (now - club.created_at).days
            for day_marker in reminder_days:
                if age_days < day_marker:
                    continue
                field_name = f"registration_reminder_{day_marker}_sent_at"
                if not hasattr(club, field_name):
                    continue
                if getattr(club, field_name):
                    continue
                if send_social_club_registration_reminder_email(club=club, day_marker=day_marker):
                    setattr(club, field_name, now)
                    club.save(update_fields=[field_name, "updated_at"])
                    sent_count += 1

        self.stdout.write(self.style.SUCCESS(f"{sent_count} Social-Club-Reminder versendet."))
