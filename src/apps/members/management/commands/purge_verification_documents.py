from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.members.models import VerificationSubmission


class Command(BaseCommand):
    help = "Loescht Verifizierungsdokumente nach Freigabe oder spaetestens nach X Tagen."

    def handle(self, *args, **options):
        retention_days = int(getattr(settings, "VERIFICATION_DOCUMENT_RETENTION_DAYS", 30))
        cutoff = timezone.now() - timedelta(days=retention_days)
        total = 0

        approved = VerificationSubmission.objects.filter(
            status=VerificationSubmission.STATUS_APPROVED,
            documents_deleted_at__isnull=True,
        )
        for submission in approved:
            if submission.purge_sensitive_documents():
                total += 1

        stale = VerificationSubmission.objects.filter(
            documents_deleted_at__isnull=True,
            updated_at__lt=cutoff,
        )
        for submission in stale:
            if submission.purge_sensitive_documents():
                total += 1

        self.stdout.write(self.style.SUCCESS(f"{total} Verifizierungsdatensaetze bereinigt."))
