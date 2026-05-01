from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.members.models import Profile


class Command(BaseCommand):
    help = "Setzt taegliche Verbrauchswerte aller Mitglieder auf 0."

    def handle(self, *args, **options):
        today = timezone.localdate()
        updated = Profile.objects.update(
            daily_used=Decimal("0.00"),
            daily_counter_date=today,
        )
        self.stdout.write(self.style.SUCCESS(f"Daily limits reset for {updated} profiles."))
