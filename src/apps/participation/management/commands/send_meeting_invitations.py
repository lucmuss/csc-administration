from django.core.management.base import BaseCommand

from apps.participation.services import MeetingService


class Command(BaseCommand):
    help = "Versendet Einladungen 14 Tage vor der Mitgliederversammlung"

    def handle(self, *args, **options):
        sent = MeetingService.send_invitations()
        self.stdout.write(self.style.SUCCESS(f"Einladungen versendet: {sent}"))
