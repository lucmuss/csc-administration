from django.core.management.base import BaseCommand

from apps.participation.services import DeadlineService


class Command(BaseCommand):
    help = "Prueft offene Registrierungen und erinnert vor der 8-Wochen-Frist"

    def handle(self, *args, **options):
        sent = DeadlineService.check_8week_deadline()
        self.stdout.write(self.style.SUCCESS(f"8-Wochen-Erinnerungen versendet: {sent}"))
