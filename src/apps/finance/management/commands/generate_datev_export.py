from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from apps.finance.services import generate_datev_export


class Command(BaseCommand):
    help = "Erzeugt DATEV-CSV Export (month|quarter|year)"

    def add_arguments(self, parser):
        parser.add_argument("--period", choices=["month", "quarter", "year"], default="month")
        parser.add_argument("--date", default=None, help="Ankerdatum YYYY-MM-DD")

    def handle(self, *args, **options):
        anchor = None
        if options["date"]:
            try:
                anchor = datetime.strptime(options["date"], "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError("--date muss YYYY-MM-DD sein") from exc

        output = generate_datev_export(period=options["period"], anchor=anchor)
        self.stdout.write(self.style.SUCCESS(f"DATEV Export erstellt: {output}"))
