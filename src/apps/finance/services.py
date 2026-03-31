import csv
import io
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone

from apps.members.models import Profile

from .models import BalanceTopUp, BalanceTransaction, Invoice, Payment, Reminder, SepaMandate


@dataclass
class DateRange:
    start: date
    end: date


def _current_profile(user):
    return Profile.objects.get(user=user)


def _quantize_amount(amount: Decimal | str | float | int) -> Decimal:
    return Decimal(str(amount)).quantize(Decimal("0.01"))


def _ensure_legacy_balance_seed(profile: Profile) -> None:
    if profile.balance_transactions.exists():
        return
    if profile.balance == Decimal("0.00"):
        return
    BalanceTransaction.objects.create(
        profile=profile,
        amount=_quantize_amount(profile.balance),
        kind=BalanceTransaction.KIND_MANUAL_ADJUSTMENT,
        note="Legacy-Guthaben uebernommen",
        reference=f"legacy-balance-{profile.id}",
    )


def sync_profile_balance(profile: Profile) -> Decimal:
    _ensure_legacy_balance_seed(profile)
    total = (
        profile.balance_transactions.aggregate(total=models.Sum("amount"))["total"]
        if hasattr(profile, "balance_transactions")
        else None
    )
    total = _quantize_amount(total or Decimal("0.00"))
    if profile.balance != total:
        profile.balance = total
        profile.save(update_fields=["balance", "updated_at"])
    return total


def add_balance_transaction(
    *,
    profile: Profile,
    amount: Decimal | str | float | int,
    kind: str,
    note: str = "",
    reference: str = "",
    created_by=None,
) -> BalanceTransaction:
    _ensure_legacy_balance_seed(profile)
    transaction_entry = BalanceTransaction.objects.create(
        profile=profile,
        amount=_quantize_amount(amount),
        kind=kind,
        note=note,
        reference=reference,
        created_by=created_by,
    )
    sync_profile_balance(profile)
    return transaction_entry


def balance_breakdown(profile: Profile) -> dict[str, Decimal]:
    totals = {
        "membership_contributions": Decimal("0.00"),
        "topups": Decimal("0.00"),
        "adjustments": Decimal("0.00"),
        "order_spend": Decimal("0.00"),
        "refunds": Decimal("0.00"),
        "current_balance": _quantize_amount(profile.balance),
        "reserved_orders": Decimal("0.00"),
        "available_balance": _quantize_amount(profile.balance),
    }
    rows = profile.balance_transactions.values("kind").annotate(total=models.Sum("amount"))
    for row in rows:
        total = _quantize_amount(row["total"] or Decimal("0.00"))
        if row["kind"] == BalanceTransaction.KIND_MEMBERSHIP_FEE:
            totals["membership_contributions"] = total
        elif row["kind"] == BalanceTransaction.KIND_TOPUP:
            totals["topups"] = total
        elif row["kind"] == BalanceTransaction.KIND_MANUAL_ADJUSTMENT:
            totals["adjustments"] = total
        elif row["kind"] == BalanceTransaction.KIND_ORDER_CHARGE:
            totals["order_spend"] = abs(total)
        elif row["kind"] == BalanceTransaction.KIND_ORDER_REFUND:
            totals["refunds"] = total
    reserved_total = (
        profile.user.orders.filter(status="reserved").aggregate(total=models.Sum("total"))["total"] or Decimal("0.00")
    )
    totals["reserved_orders"] = _quantize_amount(reserved_total)
    totals["available_balance"] = _quantize_amount(profile.balance - totals["reserved_orders"])
    return totals


def available_balance(profile: Profile) -> Decimal:
    return balance_breakdown(profile)["available_balance"]


def active_sepa_mandate(profile: Profile) -> SepaMandate | None:
    return profile.sepa_mandate or profile.sepa_mandates.filter(is_active=True).first()


def create_sepa_mandate(*, user, iban: str, bic: str, account_holder: str) -> SepaMandate:
    profile = _current_profile(user)
    normalized_iban = iban.replace(" ", "").upper()
    normalized_bic = bic.replace(" ", "").upper()
    normalized_holder = account_holder.strip()
    mandate = active_sepa_mandate(profile)
    created = False
    if mandate:
        mandate.iban = normalized_iban
        mandate.bic = normalized_bic
        mandate.account_holder = normalized_holder
        mandate.is_active = True
        mandate.save(update_fields=["iban", "bic", "account_holder", "is_active", "updated_at"])
    else:
        reference = f"CSC-{profile.member_number or profile.id}-{uuid4().hex[:10].upper()}"
        mandate = SepaMandate.objects.create(
            profile=profile,
            iban=normalized_iban,
            bic=normalized_bic,
            account_holder=normalized_holder,
            mandate_reference=reference,
        )
        created = True
    if profile.sepa_mandate_id != mandate.id:
        profile.sepa_mandate = mandate
        profile.save(update_fields=["sepa_mandate", "updated_at"])
    from apps.governance.services import record_audit_event

    record_audit_event(
        actor=user,
        domain="finance",
        action="mandate.created" if created else "mandate.updated",
        target=mandate,
        summary=(
            f"SEPA-Mandat {mandate.mandate_reference} angelegt."
            if created
            else f"SEPA-Mandat {mandate.mandate_reference} aktualisiert."
        ),
        metadata={"profile_id": profile.id},
    )
    return mandate


def ensure_seed_credit(profile: Profile, amount: Decimal = Decimal("100.00")) -> None:
    reference = f"seed-topup-{profile.user.email}"
    if not BalanceTransaction.objects.filter(profile=profile, reference=reference).exists():
        add_balance_transaction(
            profile=profile,
            amount=amount,
            kind=BalanceTransaction.KIND_TOPUP,
            note="Demo-Startguthaben",
            reference=reference,
        )


def apply_monthly_membership_credits(today: date | None = None) -> int:
    today = today or timezone.localdate()
    amount = _quantize_amount(getattr(settings, "MEMBER_MONTHLY_FEE", Decimal("24.00")))
    month_key = today.strftime("%Y-%m")
    credited = 0
    profiles = Profile.objects.filter(
        status__in=[Profile.STATUS_ACTIVE, Profile.STATUS_VERIFIED],
        is_verified=True,
    ).select_related("user", "sepa_mandate")
    for profile in profiles:
        mandate = profile.sepa_mandate or profile.sepa_mandates.filter(is_active=True).first()
        if not mandate or not mandate.is_active:
            continue
        reference = f"membership-fee-{month_key}-{profile.id}"
        if BalanceTransaction.objects.filter(profile=profile, reference=reference).exists():
            continue
        add_balance_transaction(
            profile=profile,
            amount=amount,
            kind=BalanceTransaction.KIND_MEMBERSHIP_FEE,
            note=f"Mitgliedsbeitrag {month_key}",
            reference=reference,
        )
        credited += 1
    return credited


def credit_member_balance(*, email: str, amount: Decimal | str | float | int, note: str, kind: str = BalanceTransaction.KIND_TOPUP):
    profile = Profile.objects.select_related("user").get(user__email=email)
    entry = add_balance_transaction(
        profile=profile,
        amount=amount,
        kind=kind,
        note=note,
        reference=f"manual-{uuid4().hex[:12]}",
    )
    return profile, entry


def _stripe_enabled() -> bool:
    return bool(getattr(settings, "STRIPE_SECRET_KEY", ""))


def render_invoice_pdf(invoice: Invoice) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=A4)
    width, height = A4

    pdf.setTitle(invoice.invoice_number)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(20 * mm, height - 25 * mm, f"Rechnung {invoice.invoice_number}")
    pdf.setFont("Helvetica", 10)

    member_name = invoice.profile.user.full_name or invoice.profile.user.email
    lines = [
        ("Mitglied", member_name),
        ("E-Mail", invoice.profile.user.email),
        ("Betrag", f"{invoice.amount} EUR"),
        ("Faelligkeit", invoice.due_date.strftime("%d.%m.%Y")),
        ("Status", invoice.get_status_display()),
        ("Mahnstufe", str(invoice.reminder_level)),
        ("Bestellung", f"#{invoice.order_id}" if invoice.order_id else "-"),
        ("Erstellt", timezone.localtime(invoice.created_at).strftime("%d.%m.%Y %H:%M")),
    ]

    y = height - 42 * mm
    for label, value in lines:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(20 * mm, y, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(60 * mm, y, str(value))
        y -= 7 * mm

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20 * mm, y - 4 * mm, "Leistungsumfang")
    text = pdf.beginText(20 * mm, y - 12 * mm)
    text.setFont("Helvetica", 10)
    if invoice.order_id:
        for item in invoice.order.items.select_related("strain").all():
            text.textLine(
                f"- {item.strain.name}: {item.quantity_display} zu {item.unit_price} EUR = {item.total_price} EUR"
            )
    else:
        text.textLine("Keine Bestellposition verknuepft.")
    pdf.drawText(text)

    pdf.showPage()
    pdf.save()
    return stream.getvalue()


def create_stripe_checkout_for_topup(*, user, amount: Decimal | str | float | int, success_url: str, cancel_url: str) -> BalanceTopUp:
    amount_decimal = _quantize_amount(amount)
    profile = _current_profile(user)
    topup = BalanceTopUp.objects.create(profile=profile, amount=amount_decimal)
    if not _stripe_enabled():
        topup.status = BalanceTopUp.STATUS_FAILED
        topup.failure_reason = "Stripe ist nicht konfiguriert."
        topup.save(update_fields=["status", "failure_reason", "updated_at"])
        return topup

    form_data = urllib.parse.urlencode(
        {
            "mode": "payment",
            "success_url": f"{success_url}?topup_id={topup.id}&session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": cancel_url,
            "customer_email": user.email,
            "metadata[topup_id]": str(topup.id),
            "metadata[user_email]": user.email,
            "line_items[0][price_data][currency]": "eur",
            "line_items[0][price_data][product_data][name]": "CSC Guthaben-Aufladung",
            "line_items[0][price_data][product_data][description]": f"Virtuelles Guthaben fuer {user.email}",
            "line_items[0][price_data][unit_amount]": str(int(amount_decimal * 100)),
            "line_items[0][quantity]": "1",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.stripe.com/v1/checkout/sessions",
        data=form_data,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        topup.status = BalanceTopUp.STATUS_FAILED
        topup.failure_reason = str(exc)
        topup.save(update_fields=["status", "failure_reason", "updated_at"])
        return topup

    topup.checkout_session_id = payload.get("id", "")
    topup.checkout_url = payload.get("url", "")
    topup.save(update_fields=["checkout_session_id", "checkout_url", "updated_at"])
    return topup


def finalize_stripe_topup(*, topup: BalanceTopUp, session_id: str | None = None) -> BalanceTopUp:
    if topup.status == BalanceTopUp.STATUS_COMPLETED:
        return topup
    session_id = session_id or topup.checkout_session_id
    if not session_id or not _stripe_enabled():
        return topup

    request = urllib.request.Request(
        f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
        headers={"Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        topup.failure_reason = str(exc)
        topup.save(update_fields=["failure_reason", "updated_at"])
        return topup

    payment_status = payload.get("payment_status")
    if payment_status == "paid":
        add_balance_transaction(
            profile=topup.profile,
            amount=topup.amount,
            kind=BalanceTransaction.KIND_TOPUP,
            note="Stripe-Aufladung",
            reference=f"stripe-session-{session_id}",
        )
        topup.status = BalanceTopUp.STATUS_COMPLETED
        topup.completed_at = timezone.now()
        topup.checkout_session_id = session_id
        topup.save(update_fields=["status", "completed_at", "checkout_session_id", "updated_at"])
    return topup


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


def settle_order_with_balance(*, order) -> Payment:
    profile = _current_profile(order.member)
    amount = _quantize_amount(order.total)
    if available_balance(profile) < amount:
        raise ValueError("Nicht genug verfuegbares Guthaben fuer die Ausgabe.")
    add_balance_transaction(
        profile=profile,
        amount=-amount,
        kind=BalanceTransaction.KIND_ORDER_CHARGE,
        note=f"Bestellung #{order.id} ausgegeben",
        reference=f"order-{order.id}-charge",
        created_by=order.member,
    )
    profile.refresh_from_db(fields=["balance"])
    order.paid_with_balance = amount
    order.save(update_fields=["paid_with_balance", "updated_at"])
    invoice = getattr(order, "invoice", None) or create_invoice_for_order(order=order)
    invoice.status = Invoice.STATUS_PAID
    invoice.save(update_fields=["status", "updated_at"])
    payment = Payment.objects.create(
        invoice=invoice,
        profile=profile,
        amount=amount,
        method=Payment.METHOD_BALANCE,
        status=Payment.STATUS_COLLECTED,
        scheduled_for=timezone.localdate(),
        collected_at=timezone.now(),
    )
    return payment


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
            from_email=settings.DEFAULT_FROM_EMAIL,
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
            from_email=settings.DEFAULT_FROM_EMAIL,
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
