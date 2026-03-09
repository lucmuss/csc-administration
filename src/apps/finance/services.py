import csv
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.members.models import Profile

from .models import Invoice, Payment, Reminder, SepaMandate


@dataclass
class DateRange:
    start: date
    end: date


def _current_profile(user):
    return Profile.objects.get(user=user)


def create_sepa_mandate(*, user, iban: str, bic: str, account_holder: str) -> SepaMandate:
    profile = _current_profile(user)
    reference = f"CSC-{profile.member_number or profile.id}-{uuid4().hex[:10].upper()}"
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban=iban.replace(" ", "").upper(),
        bic=bic.replace(" ", "").upper(),
        account_holder=account_holder.strip(),
        mandate_reference=reference,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    from apps.governance.services import record_audit_event

    record_audit_event(
        actor=user,
        domain="finance",
        action="mandate.created",
        target=mandate,
        summary=f"SEPA-Mandat {mandate.mandate_reference} angelegt.",
        metadata={"profile_id": profile.id},
    )
    return mandate


def create_invoice_for_order(*, order) -> Invoice:
    profile = _current_profile(order.member)
    invoice = Invoice.objects.create(
        profile=profile,
        order=order,
        invoice_number=f"INV-{order.id:06d}",
        amount=order.total,
        due_date=timezone.localdate(),
        status=Invoice.STATUS_PAID if order.paid_with_balance >= order.total else Invoice.STATUS_OPEN,
    )
    Payment.objects.create(
        invoice=invoice,
        profile=profile,
        amount=order.total,
        method=Payment.METHOD_BALANCE,
        status=Payment.STATUS_COLLECTED,
        scheduled_for=timezone.localdate(),
        collected_at=timezone.now(),
    )
    from apps.governance.services import record_audit_event

    record_audit_event(
        actor=order.member,
        domain="finance",
        action="invoice.created",
        target=invoice,
        summary=f"Rechnung {invoice.invoice_number} fuer Bestellung {order.id} erzeugt.",
        metadata={"order_id": order.id, "amount": str(invoice.amount)},
    )
    return invoice


def schedule_sepa_payment(*, invoice: Invoice, scheduled_for: date | None = None) -> Payment | None:
    if invoice.status != Invoice.STATUS_OPEN:
        return None

    mandate = invoice.profile.sepa_mandate
    if not mandate:
        mandate = SepaMandate.objects.filter(active_for_profile__id=invoice.profile_id, is_active=True).first()
    if not mandate or not mandate.is_active:
        return None

    scheduled_for = scheduled_for or timezone.localdate()
    payment, _ = Payment.objects.get_or_create(
        invoice=invoice,
        method=Payment.METHOD_SEPA,
        status=Payment.STATUS_PENDING,
        defaults={
            "profile": invoice.profile,
            "mandate": mandate,
            "amount": invoice.amount,
            "scheduled_for": scheduled_for,
        },
    )
    return payment


def send_sepa_prenotifications(today: date | None = None) -> int:
    today = today or timezone.localdate()
    target = today + timedelta(days=1)
    payments = Payment.objects.select_related("profile__user", "invoice").filter(
        method=Payment.METHOD_SEPA,
        status=Payment.STATUS_PENDING,
        scheduled_for=target,
    )
    sent = 0
    for payment in payments:
        send_mail(
            subject="SEPA Vorabankuendigung",
            message=(
                f"Ihre Lastschrift ueber {payment.amount} EUR fuer {payment.invoice.invoice_number} "
                f"wird am {payment.scheduled_for:%d.%m.%Y} eingezogen."
            ),
            from_email="noreply@csc.local",
            recipient_list=[payment.profile.user.email],
            fail_silently=True,
        )
        payment.status = Payment.STATUS_PRNOTIFIED
        payment.prenotified_at = timezone.now()
        payment.save(update_fields=["status", "prenotified_at", "updated_at"])
        from apps.governance.services import record_audit_event

        record_audit_event(
            actor=None,
            domain="finance",
            action="payment.prenotified",
            target=payment,
            summary=f"Vorabankuendigung fuer {payment.invoice.invoice_number} versendet.",
            metadata={"payment_id": payment.id, "scheduled_for": payment.scheduled_for.isoformat()},
        )
        sent += 1
    return sent


def collect_due_sepa_payments(today: date | None = None) -> int:
    today = today or timezone.localdate()
    batch_id = f"SEPA-{today:%Y%m%d}-{uuid4().hex[:8].upper()}"
    due = Payment.objects.select_related("invoice").filter(
        method=Payment.METHOD_SEPA,
        status__in=[Payment.STATUS_PENDING, Payment.STATUS_PRNOTIFIED],
        scheduled_for__lte=today,
    )

    collected = 0
    with transaction.atomic():
        for payment in due.select_for_update():
            if not payment.mandate or not payment.mandate.is_active:
                payment.status = Payment.STATUS_FAILED
                payment.failure_reason = "Kein aktives Mandat"
                payment.save(update_fields=["status", "failure_reason", "updated_at"])
                from apps.governance.services import record_audit_event

                record_audit_event(
                    actor=None,
                    domain="finance",
                    action="payment.failed",
                    target=payment,
                    summary=f"SEPA-Einzug fuer {payment.invoice.invoice_number} fehlgeschlagen.",
                    metadata={"reason": payment.failure_reason},
                )
                continue

            payment.status = Payment.STATUS_COLLECTED
            payment.collected_at = timezone.now()
            payment.sepa_batch_id = batch_id
            payment.save(update_fields=["status", "collected_at", "sepa_batch_id", "updated_at"])

            invoice = payment.invoice
            invoice.status = Invoice.STATUS_PAID
            invoice.save(update_fields=["status", "updated_at"])
            from apps.governance.services import record_audit_event

            record_audit_event(
                actor=None,
                domain="finance",
                action="payment.collected",
                target=payment,
                summary=f"SEPA-Einzug fuer {invoice.invoice_number} erfolgreich verbucht.",
                metadata={"batch_id": batch_id, "amount": str(payment.amount)},
            )
            collected += 1
    return collected


def handle_payment_return(*, payment: Payment, reason: str = "Ruecklaeufer") -> None:
    if payment.status != Payment.STATUS_COLLECTED:
        return

    payment.status = Payment.STATUS_RETURNED
    payment.returned_at = timezone.now()
    payment.failure_reason = reason
    payment.save(update_fields=["status", "returned_at", "failure_reason", "updated_at"])

    invoice = payment.invoice
    invoice.status = Invoice.STATUS_OPEN
    invoice.save(update_fields=["status", "updated_at"])
    from apps.governance.services import record_audit_event

    record_audit_event(
        actor=None,
        domain="finance",
        action="payment.returned",
        target=payment,
        summary=f"Ruecklaeufer fuer {invoice.invoice_number} erfasst.",
        metadata={"reason": reason},
    )


def _apply_reminder_fee(invoice: Invoice, fee_amount: Decimal) -> None:
    if fee_amount <= Decimal("0.00"):
        return
    invoice.amount += fee_amount


def _maybe_lock_member(invoice: Invoice, level: int) -> None:
    if level < Reminder.LEVEL_4:
        return
    profile = invoice.profile
    profile.is_locked_for_orders = True
    profile.save(update_fields=["is_locked_for_orders", "updated_at"])
    invoice.blocked_member = True


def send_due_reminders(today: date | None = None) -> int:
    today = today or timezone.localdate()
    sent = 0

    invoices = Invoice.objects.select_related("profile").filter(status=Invoice.STATUS_OPEN)
    for invoice in invoices:
        next_date = invoice.next_reminder_date()
        if not next_date or next_date > today:
            continue
        if invoice.reminder_level >= Reminder.LEVEL_4:
            continue

        new_level = invoice.reminder_level + 1
        fee = Reminder.FEE_BY_LEVEL[new_level]

        if Reminder.objects.filter(invoice=invoice, level=new_level).exists():
            continue

        _apply_reminder_fee(invoice, fee)
        invoice.reminder_level = new_level
        _maybe_lock_member(invoice, new_level)
        invoice.save(update_fields=["amount", "reminder_level", "blocked_member", "updated_at"])

        Reminder.objects.create(
            invoice=invoice,
            level=new_level,
            fee_amount=fee,
            note=f"Automatisch versendet am {today:%d.%m.%Y}",
        )

        send_mail(
            subject=f"Mahnung Stufe {new_level} - {invoice.invoice_number}",
            message=(
                f"Rechnung {invoice.invoice_number} ist ueberfaellig. "
                f"Mahnstufe {new_level}, offene Summe: {invoice.amount} EUR."
            ),
            from_email="noreply@csc.local",
            recipient_list=[invoice.profile.user.email],
            fail_silently=True,
        )
        from apps.governance.services import record_audit_event

        record_audit_event(
            actor=None,
            domain="finance",
            action="reminder.sent",
            target=invoice,
            summary=f"Mahnung Stufe {new_level} fuer {invoice.invoice_number} versendet.",
            metadata={"level": new_level, "amount": str(invoice.amount)},
        )
        sent += 1

    return sent


def resolve_date_range(period: str, anchor: date | None = None) -> DateRange:
    anchor = anchor or timezone.localdate()

    if period == "month":
        start = anchor.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1) - timedelta(days=1)
        return DateRange(start=start, end=end)

    if period == "quarter":
        quarter_start_month = ((anchor.month - 1) // 3) * 3 + 1
        start = anchor.replace(month=quarter_start_month, day=1)
        if quarter_start_month == 10:
            end = start.replace(year=start.year + 1, month=1) - timedelta(days=1)
        else:
            end = start.replace(month=quarter_start_month + 3) - timedelta(days=1)
        return DateRange(start=start, end=end)

    if period == "year":
        return DateRange(
            start=anchor.replace(month=1, day=1),
            end=anchor.replace(month=12, day=31),
        )

    raise ValueError("period muss month, quarter oder year sein")


def generate_datev_export(*, period: str = "month", anchor: date | None = None) -> Path:
    drange = resolve_date_range(period, anchor)
    invoices = Invoice.objects.select_related("profile__user").filter(
        created_at__date__gte=drange.start,
        created_at__date__lte=drange.end,
    )

    export_dir = Path(settings.EXPORT_ROOT)
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"datev_{period}_{drange.start:%Y%m%d}_{drange.end:%Y%m%d}.csv"
    target = export_dir / filename

    with target.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Belegdatum",
            "Belegnummer",
            "Konto",
            "Gegenkonto",
            "Betrag",
            "Buchungstext",
            "Mitglied",
            "Status",
        ])
        for invoice in invoices:
            writer.writerow([
                invoice.created_at.date().isoformat(),
                invoice.invoice_number,
                "1200",
                "8400",
                f"{invoice.amount:.2f}",
                "Mitgliedsverkauf",
                invoice.profile.user.email,
                invoice.status,
            ])

    return target
