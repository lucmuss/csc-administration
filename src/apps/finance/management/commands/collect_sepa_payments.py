from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.finance.models import Invoice, Payment
from apps.finance.services import collect_due_sepa_payments, schedule_sepa_payment, send_sepa_prenotifications


class Command(BaseCommand):
    help = "Versendet SEPA-Vorabankuendigungen (D+1) und zieht faellige Lastschriften ein"

    def handle(self, *args, **options):
        created = 0
        for invoice in Invoice.objects.select_related("profile__sepa_mandate").filter(status=Invoice.STATUS_OPEN):
            if Payment.objects.filter(invoice=invoice, method=Payment.METHOD_SEPA).exclude(
                status=Payment.STATUS_FAILED
            ).exists():
                continue
            if schedule_sepa_payment(invoice=invoice, scheduled_for=timezone.localdate() + timedelta(days=1)):
                created += 1

        prenotified = send_sepa_prenotifications()
        collected = collect_due_sepa_payments()
        self.stdout.write(
            self.style.SUCCESS(
                f"SEPA verarbeitet: Angelegt={created}, Vorabankuendigungen={prenotified}, Eingezogen={collected}"
            )
        )
