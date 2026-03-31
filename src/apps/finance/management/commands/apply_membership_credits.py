from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.finance.services import apply_monthly_membership_credits


class Command(BaseCommand):
    help = "Applies the monthly membership fee credit to eligible members exactly once per month."

    def handle(self, *args, **options):
        credited = apply_monthly_membership_credits(today=timezone.localdate())
        self.stdout.write(self.style.SUCCESS(f"Applied monthly membership credits to {credited} profiles."))
