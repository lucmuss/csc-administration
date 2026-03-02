from django.core.management.base import BaseCommand

from apps.finance.services import send_due_reminders


class Command(BaseCommand):
    help = "Versendet faellige Erinnerungen/Mahnungen fuer offene Rechnungen"

    def handle(self, *args, **options):
        sent = send_due_reminders()
        self.stdout.write(self.style.SUCCESS(f"Mahnungen versendet: {sent}"))
