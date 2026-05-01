from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import Order


class Command(BaseCommand):
    help = "Setzt veraltete Reservierungen auf abgelaufen."

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(hours=48)
        expired = Order.objects.filter(status=Order.STATUS_RESERVED, created_at__lt=threshold)
        count = expired.update(status=Order.STATUS_EXPIRED, updated_at=timezone.now())
        self.stdout.write(self.style.SUCCESS(f"{count} Reservierungen als abgelaufen markiert."))
