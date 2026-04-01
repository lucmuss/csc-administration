from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.finance.models import UploadedInvoice
from apps.finance.services import import_uploaded_invoices_from_directory


class Command(BaseCommand):
    help = "Imports invoice files from data/invoices into the finance archive for GUI testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--directory",
            default=str(Path(settings.BASE_DIR) / "data" / "invoices"),
            help="Directory with invoice files (PDF/image/txt).",
        )
        parser.add_argument(
            "--direction",
            default=UploadedInvoice.DIRECTION_INCOMING,
            choices=[UploadedInvoice.DIRECTION_INCOMING, UploadedInvoice.DIRECTION_OUTGOING],
            help="Default invoice direction for imported files.",
        )

    def handle(self, *args, **options):
        directory = Path(options["directory"])
        operator = User.objects.filter(role__in=[User.ROLE_BOARD, User.ROLE_STAFF]).order_by("id").first()
        imported = import_uploaded_invoices_from_directory(
            directory=directory,
            created_by=operator,
            assigned_to=operator,
            default_direction=options["direction"],
            analyze=True,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(imported)} invoice files from {directory} into the archive."
            )
        )
