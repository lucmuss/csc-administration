from django.core.management.base import BaseCommand

from apps.participation.services import LimitResetService


class Command(BaseCommand):
    help = "Setzt monatliche Verbrauchslimits fuer alle Mitglieder zurueck"

    def handle(self, *args, **options):
        updated = LimitResetService.reset_monthly()
        self.stdout.write(self.style.SUCCESS(f"Monatliche Limits zurueckgesetzt: {updated}"))
