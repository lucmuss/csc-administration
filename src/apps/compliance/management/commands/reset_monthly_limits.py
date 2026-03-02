from django.core.management.base import BaseCommand

from apps.compliance.services import reset_monthly_limits


class Command(BaseCommand):
    help = "Setzt monatliche Verbrauchslimits fuer alle Mitglieder zurueck"

    def handle(self, *args, **options):
        updated = reset_monthly_limits()
        self.stdout.write(self.style.SUCCESS(f"Monatliche Limits zurueckgesetzt: {updated}"))
