from django.core.management.base import BaseCommand

from apps.orders.services import release_expired_reservations


class Command(BaseCommand):
    help = "Loest abgelaufene Reservierungen nach 48 Stunden auf"

    def handle(self, *args, **options):
        released = release_expired_reservations()
        self.stdout.write(self.style.SUCCESS(f"Abgelaufene Reservierungen aufgeloest: {released}"))
