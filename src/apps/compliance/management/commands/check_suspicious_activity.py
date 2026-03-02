from django.core.management.base import BaseCommand

from apps.compliance.services import detect_suspicious_activity


class Command(BaseCommand):
    help = "Prueft Profile auf verdaechtigen Monatsverbrauch > 50g"

    def handle(self, *args, **options):
        detected = detect_suspicious_activity()
        self.stdout.write(self.style.SUCCESS(f"Verdaechtige Aktivitaeten geprueft: {detected}"))
