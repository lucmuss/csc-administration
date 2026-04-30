from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.finance.services import apply_monthly_membership_credits


class Command(BaseCommand):
    help = "Zieht Mitgliedsbeitraege standardmaessig zur Monatsmitte (Tag 15) ein und bucht sie als Guthaben."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Fuehrt den Einzug unabhaengig vom aktuellen Kalendertag aus.",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        if not options.get("force") and today.day != 15:
            self.stdout.write(self.style.WARNING(f"Kein Lauf: heute ist {today:%d.%m.%Y}. Standard-Einzug erfolgt am 15."))
            return
        credited = apply_monthly_membership_credits(today=today)
        self.stdout.write(self.style.SUCCESS(f"Mitgliedsbeitraege erfolgreich verbucht: {credited}"))
