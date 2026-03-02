from django.core.management.base import BaseCommand

from apps.participation.services import MeetingService


class Command(BaseCommand):
    help = "Versendet Erinnerungen 2 Tage vor der Mitgliederversammlung"

    def handle(self, *args, **options):
        sent = MeetingService.send_reminders()
        self.stdout.write(self.style.SUCCESS(f"Erinnerungen versendet: {sent}"))
