from django.core.management.base import BaseCommand

from apps.finance.services import collect_due_sepa_payments, send_sepa_prenotifications


class Command(BaseCommand):
    help = "Versendet SEPA-Vorabankuendigungen (D+1) und zieht faellige Lastschriften ein"

    def handle(self, *args, **options):
        prenotified = send_sepa_prenotifications()
        collected = collect_due_sepa_payments()
        self.stdout.write(
            self.style.SUCCESS(
                f"SEPA verarbeitet: Vorabankuendigungen={prenotified}, Eingezogen={collected}"
            )
        )
