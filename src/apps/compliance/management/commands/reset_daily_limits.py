from django.core.management.base import BaseCommand

from apps.compliance.services import reset_daily_limits


class Command(BaseCommand):
    help = "Setzt taegliche Verbrauchslimits fuer alle Mitglieder zurueck"

    def handle(self, *args, **options):
        updated = reset_daily_limits()
        self.stdout.write(self.style.SUCCESS(f"Taegliche Limits zurueckgesetzt: {updated}"))
