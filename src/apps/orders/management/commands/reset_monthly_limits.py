from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.members.models import Profile


class Command(BaseCommand):
    help = "Setzt monatliche Verbrauchswerte aller Mitglieder auf 0."

    def handle(self, *args, **options):
        month_key = timezone.localdate().strftime("%Y-%m")
        updated = Profile.objects.update(
            monthly_used=Decimal("0.00"),
            monthly_counter_key=month_key,
        )
        self.stdout.write(self.style.SUCCESS(f"Monthly limits reset for {updated} profiles."))
