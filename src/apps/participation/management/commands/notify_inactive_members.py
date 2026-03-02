from django.core.management.base import BaseCommand

from apps.participation.services import InactivityService


class Command(BaseCommand):
    help = "Benachrichtigt Mitglieder nach 60 Tagen ohne Bestellung"

    def handle(self, *args, **options):
        sent = InactivityService.notify_inactive_members()
        self.stdout.write(self.style.SUCCESS(f"Inaktivitaets-Benachrichtigungen: {sent}"))
