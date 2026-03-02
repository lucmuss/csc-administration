from django.core.management.base import BaseCommand

from apps.participation.services import LimitResetService


class Command(BaseCommand):
    help = "Setzt taegliche Verbrauchslimits fuer alle Mitglieder zurueck"

    def handle(self, *args, **options):
        updated = LimitResetService.reset_daily()
        self.stdout.write(self.style.SUCCESS(f"Taegliche Limits zurueckgesetzt: {updated}"))
