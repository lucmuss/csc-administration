from django.core.management.base import BaseCommand

from apps.governance.services import send_due_meeting_notifications


class Command(BaseCommand):
    help = "Versendet faellige Einladungen und Reminder fuer Mitgliederversammlungen."

    def handle(self, *args, **options):
        result = send_due_meeting_notifications()
        self.stdout.write(
            self.style.SUCCESS(
                f"Meeting-Benachrichtigungen versendet: {result['invitations']} Einladungen, {result['reminders']} Reminder."
            )
        )
