import csv
import io
import json
import base64
import mimetypes
import re
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
from PIL import Image, ImageOps
from pypdf import PdfReader

from apps.members.models import Profile

from .models import BalanceTopUp, BalanceTransaction, Invoice, Payment, Reminder, SepaMandate, UploadedInvoice


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
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=A4)
    width, height = A4

    pdf.setTitle(invoice.invoice_number)
    top_y = height - 20 * mm
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(20 * mm, top_y, settings.CLUB_NAME)
    pdf.setFont("Helvetica", 9)
    address_lines = [line.strip() for line in (settings.CLUB_CONTACT_ADDRESS or "").splitlines() if line.strip()]
    for index, line in enumerate(address_lines[:4], start=1):
        pdf.drawString(20 * mm, top_y - (index * 5 * mm), line)
    pdf.drawRightString(width - 20 * mm, top_y, f"Rechnung {invoice.invoice_number}")
    pdf.setFont("Helvetica", 9)
    pdf.drawRightString(width - 20 * mm, top_y - 6 * mm, f"Erstellt am {timezone.localtime(invoice.created_at).strftime('%d.%m.%Y %H:%M')}")
    pdf.drawRightString(width - 20 * mm, top_y - 11 * mm, f"Faellig am {invoice.due_date.strftime('%d.%m.%Y')}")
    pdf.drawRightString(width - 20 * mm, top_y - 16 * mm, "Rechnungsart Mitgliedsabrechnung")

    tax_note = "Umsatzsteuer nach Vereins- und Leistungsart pruefen."
    if getattr(settings, "CLUB_VAT_ID", ""):
        tax_note = f"USt-ID: {settings.CLUB_VAT_ID}"
    elif getattr(settings, "CLUB_TAX_NUMBER", ""):
        tax_note = f"Steuernummer: {settings.CLUB_TAX_NUMBER}"

    member_name = invoice.profile.user.full_name or invoice.profile.user.email
    member_address = [
        invoice.profile.street_address or "",
        " ".join(part for part in [invoice.profile.postal_code, invoice.profile.city] if part),
    ]
    invoice_meta = [
        ("Mitglied", member_name),
        ("Mitgliedsnummer", str(invoice.profile.member_number or "-")),
        ("E-Mail", invoice.profile.user.email),
        ("Status", invoice.get_status_display()),
        ("Mahnstufe", str(invoice.reminder_level)),
        ("Bestellung", f"#{invoice.order_id}" if invoice.order_id else "-"),
        ("Leistungsdatum", invoice.due_date.strftime("%d.%m.%Y")),
        ("Zahlziel", f"zahlbar bis {invoice.due_date.strftime('%d.%m.%Y')}"),
    ]

    y = height - 62 * mm
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20 * mm, y, "Rechnungsempfaenger")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, y - 6 * mm, member_name)
    if member_address[0]:
        pdf.drawString(20 * mm, y - 11 * mm, member_address[0])
    if member_address[1]:
        pdf.drawString(20 * mm, y - 16 * mm, member_address[1])

    meta_y = y
    for label, value in invoice_meta:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(105 * mm, meta_y, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(145 * mm, meta_y, str(value))
        meta_y -= 6 * mm

    pdf.setFont("Helvetica-Bold", 10)
    table_y = y - 34 * mm
    pdf.drawString(20 * mm, table_y, "Leistungsumfang")
    pdf.setStrokeColor(colors.HexColor("#c7d7cd"))
    pdf.line(20 * mm, table_y - 3 * mm, width - 20 * mm, table_y - 3 * mm)
    header_y = table_y - 10 * mm
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(20 * mm, header_y, "Position")
    pdf.drawString(95 * mm, header_y, "Menge")
    pdf.drawString(125 * mm, header_y, "Einzelpreis")
    pdf.drawRightString(width - 20 * mm, header_y, "Summe")
    row_y = header_y - 6 * mm
    pdf.setFont("Helvetica", 9)
    if invoice.order_id:
        for item in invoice.order.items.select_related("strain").all():
            pdf.drawString(20 * mm, row_y, item.strain.name[:42])
            pdf.drawString(95 * mm, row_y, item.quantity_display)
            pdf.drawString(125 * mm, row_y, f"{item.unit_price} EUR")
            pdf.drawRightString(width - 20 * mm, row_y, f"{item.total_price} EUR")
            row_y -= 6 * mm
    else:
        pdf.drawString(20 * mm, row_y, "Keine Bestellposition verknuepft.")
        row_y -= 6 * mm

    pdf.line(20 * mm, row_y - 2 * mm, width - 20 * mm, row_y - 2 * mm)
    subtotal = invoice.amount
    tax_amount = Decimal("0.00")
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(110 * mm, row_y - 8 * mm, f"Zwischensumme: {subtotal} EUR")
    pdf.drawString(110 * mm, row_y - 14 * mm, f"Steuer: {tax_amount} EUR")
    pdf.drawRightString(width - 20 * mm, row_y - 20 * mm, f"Gesamtbetrag: {invoice.amount} EUR")
    pdf.setFont("Helvetica", 8)
    footer_lines = [
        settings.CLUB_CONTACT_EMAIL,
        settings.CLUB_CONTACT_PHONE,
        settings.CLUB_REGISTER_ENTRY,
        settings.CLUB_REGISTER_COURT,
        settings.CLUB_TAX_NUMBER,
        settings.CLUB_VAT_ID,
        settings.CLUB_SUPERVISORY_AUTHORITY,
        settings.CLUB_CONTENT_RESPONSIBLE or settings.CLUB_RESPONSIBLE_PERSON,
    ]
    note_y = row_y - 32 * mm
    pdf.setFont("Helvetica", 8)
    pdf.drawString(20 * mm, note_y, "Hinweise")
    notes = pdf.beginText(20 * mm, note_y - 5 * mm)
    notes.setFont("Helvetica", 8)
    notes.textLine(tax_note)
    notes.textLine(f"Leistungszeitraum und Rechnungsdatum entsprechen der Bestellung #{invoice.order_id}." if invoice.order_id else "Leistungszeitraum siehe Rechnungs- und Mitgliedsdaten.")
    notes.textLine(f"Bitte ueberweise offene Betraege bis spaetestens {invoice.due_date.strftime('%d.%m.%Y')}.")
    pdf.drawText(notes)

    footer_y = 18 * mm
    pdf.line(20 * mm, footer_y + 8 * mm, width - 20 * mm, footer_y + 8 * mm)
    footer_text = pdf.beginText(20 * mm, footer_y)
    footer_text.setFont("Helvetica", 8)
    footer_text.textLine(settings.CLUB_NAME)
    for line in address_lines:
        footer_text.textLine(line)
    for line in footer_lines:
        if line:
            footer_text.textLine(str(line))
    pdf.drawText(footer_text)

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


def _safe_decimal(value, default: str = "0.00") -> Decimal:
    text = str(value or "").strip().replace(",", ".")
    try:
        return Decimal(text).quantize(Decimal("0.01"))
    except Exception:
        return Decimal(default)


def _parse_iso_date(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return timezone.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _extract_uploaded_invoice_text(uploaded_invoice: UploadedInvoice) -> str:
    uploaded_invoice.document.open("rb")
    try:
        suffix = Path(uploaded_invoice.document.name).suffix.lower()
        if suffix == ".pdf":
            reader = PdfReader(uploaded_invoice.document)
            parts = [(page.extract_text() or "").strip() for page in reader.pages]
            return "\n\n".join(part for part in parts if part).strip()
        if suffix == ".txt":
            return uploaded_invoice.document.read().decode("utf-8", errors="replace").strip()
        return ""
    finally:
        uploaded_invoice.document.close()


def _local_invoice_fallback(uploaded_invoice: UploadedInvoice, extracted_text: str) -> UploadedInvoice:
    text = extracted_text or uploaded_invoice.title or Path(uploaded_invoice.document.name).stem
    invoice_number_match = re.search(r"\b(?:rechnungsnummer|rechnung|invoice)[^A-Z0-9]{0,8}([A-Z0-9-]{3,})", text, re.IGNORECASE)
    amount_match = re.search(r"(\d{1,6}[.,]\d{2})\s*(?:EUR|€)", text, re.IGNORECASE)
    date_match = re.search(r"\b(\d{2}[./]\d{2}[./]\d{4}|\d{4}-\d{2}-\d{2})\b", text)

    uploaded_invoice.invoice_number = uploaded_invoice.invoice_number or (
        invoice_number_match.group(1).strip() if invoice_number_match else ""
    )
    uploaded_invoice.issue_date = uploaded_invoice.issue_date or (
        _parse_iso_date(date_match.group(1)) if date_match else None
    )
    gross = _safe_decimal(amount_match.group(1)) if amount_match else uploaded_invoice.amount_gross
    uploaded_invoice.amount_gross = gross
    uploaded_invoice.amount_net = uploaded_invoice.amount_net or gross
    uploaded_invoice.amount_tax = uploaded_invoice.amount_tax or Decimal("0.00")
    uploaded_invoice.ai_summary = uploaded_invoice.ai_summary or "Lokale Analyse aus Dateitext/Filename erzeugt."
    uploaded_invoice.ai_payload = {
        "source": "local-fallback",
        "document_name": Path(uploaded_invoice.document.name).name,
        "invoice_number": uploaded_invoice.invoice_number,
        "issue_date": uploaded_invoice.issue_date.isoformat() if uploaded_invoice.issue_date else "",
        "amount_gross": str(uploaded_invoice.amount_gross),
        "summary": uploaded_invoice.ai_summary,
    }
    uploaded_invoice.extraction_status = UploadedInvoice.EXTRACTION_SUCCESS
    uploaded_invoice.extraction_error = ""
    uploaded_invoice.extracted_at = timezone.now()
    uploaded_invoice.save(
        update_fields=[
            "invoice_number",
            "issue_date",
            "amount_net",
            "amount_tax",
            "amount_gross",
            "ai_summary",
            "ai_payload",
            "extraction_status",
            "extraction_error",
            "extracted_at",
            "updated_at",
        ]
    )
    return uploaded_invoice


def _invoice_file_message(uploaded_invoice: UploadedInvoice):
    uploaded_invoice.document.open("rb")
    try:
        raw = uploaded_invoice.document.read()
    finally:
        uploaded_invoice.document.close()
    mime_type = mimetypes.guess_type(uploaded_invoice.document.name)[0] or "application/octet-stream"
    if mime_type.startswith("image/"):
        try:
            image = Image.open(io.BytesIO(raw))
            image = ImageOps.exif_transpose(image)
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            elif image.mode == "L":
                image = image.convert("RGB")
            max_width = 1800
            if image.width > max_width:
                ratio = max_width / float(image.width)
                image = image.resize((max_width, int(image.height * ratio)))
            normalized = io.BytesIO()
            image.save(normalized, format="PNG", optimize=True)
            raw = normalized.getvalue()
            mime_type = "image/png"
        except Exception:
            mime_type = mime_type or "image/jpeg"
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64.b64encode(raw).decode('ascii')}",
            },
        }
    return None


def _extract_json_payload(raw_content: str) -> dict:
    text = (raw_content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _openrouter_headers() -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    if getattr(settings, "OPENROUTER_SITE_URL", ""):
        headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
    if getattr(settings, "OPENROUTER_APP_NAME", ""):
        headers["X-Title"] = settings.OPENROUTER_APP_NAME
    return headers


def analyze_uploaded_invoice(uploaded_invoice: UploadedInvoice) -> UploadedInvoice:
    extracted_text = _extract_uploaded_invoice_text(uploaded_invoice)
    file_message = _invoice_file_message(uploaded_invoice)
    uploaded_invoice.extraction_status = UploadedInvoice.EXTRACTION_PENDING
    uploaded_invoice.extraction_error = ""
    uploaded_invoice.ai_payload = {
        "source": "pending",
        "document_name": Path(uploaded_invoice.document.name).name,
    }
    uploaded_invoice.save(update_fields=["extraction_status", "extraction_error", "ai_payload", "updated_at"])

    if not settings.OPENROUTER_API_KEY:
        if extracted_text:
            return _local_invoice_fallback(uploaded_invoice, extracted_text)
        uploaded_invoice.extraction_status = UploadedInvoice.EXTRACTION_FAILED
        uploaded_invoice.extraction_error = "OPENROUTER_API_KEY ist nicht gesetzt."
        uploaded_invoice.ai_payload = {
            "source": "missing-openrouter-key",
            "document_name": Path(uploaded_invoice.document.name).name,
            "text_extracted": False,
        }
        uploaded_invoice.extracted_at = timezone.now()
        uploaded_invoice.save(update_fields=["extraction_status", "extraction_error", "ai_payload", "extracted_at", "updated_at"])
        return uploaded_invoice

    prompt = (
        "Extrahiere aus dieser Rechnung die wichtigsten Daten und antworte ausschliesslich als JSON mit den Schluesseln "
        "invoice_number, vendor_name, customer_name, issue_date, due_date, amount_net, amount_tax, amount_gross, currency, summary. "
        "Nutze ISO-Datumsformat YYYY-MM-DD. Wenn etwas fehlt, gib leere Strings oder 0 zurueck."
    )
    if extracted_text:
        prompt += f"\n\nBereits lokal extrahierter Text:\n{extracted_text[:12000]}"

    content = [{"type": "text", "text": prompt}]
    if file_message:
        content.append(file_message)

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
        "temperature": 0,
    }
    request = urllib.request.Request(
        f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=_openrouter_headers(),
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        raw_content = body["choices"][0]["message"]["content"]
        extracted = _extract_json_payload(raw_content)
    except Exception as exc:
        if extracted_text:
            return _local_invoice_fallback(uploaded_invoice, extracted_text)
        uploaded_invoice.extraction_status = UploadedInvoice.EXTRACTION_FAILED
        uploaded_invoice.extraction_error = str(exc)[:255]
        uploaded_invoice.ai_payload = {
            "source": "openrouter-error",
            "document_name": Path(uploaded_invoice.document.name).name,
            "error": str(exc)[:255],
            "text_extracted": False,
        }
        uploaded_invoice.extracted_at = timezone.now()
        uploaded_invoice.save(update_fields=["extraction_status", "extraction_error", "ai_payload", "extracted_at", "updated_at"])
        return uploaded_invoice

    uploaded_invoice.invoice_number = str(extracted.get("invoice_number", "")).strip()
    uploaded_invoice.vendor_name = str(extracted.get("vendor_name", "")).strip()
    uploaded_invoice.customer_name = str(extracted.get("customer_name", "")).strip()
    uploaded_invoice.issue_date = _parse_iso_date(extracted.get("issue_date"))
    uploaded_invoice.due_date = _parse_iso_date(extracted.get("due_date"))
    uploaded_invoice.amount_net = _safe_decimal(extracted.get("amount_net"))
    uploaded_invoice.amount_tax = _safe_decimal(extracted.get("amount_tax"))
    uploaded_invoice.amount_gross = _safe_decimal(extracted.get("amount_gross"))
    uploaded_invoice.currency = str(extracted.get("currency") or "EUR").strip().upper()[:8] or "EUR"
    uploaded_invoice.ai_summary = str(extracted.get("summary", "")).strip()
    uploaded_invoice.ai_payload = extracted
    uploaded_invoice.extraction_status = UploadedInvoice.EXTRACTION_SUCCESS
    uploaded_invoice.extraction_error = ""
    uploaded_invoice.extracted_at = timezone.now()
    uploaded_invoice.save(
        update_fields=[
            "invoice_number",
            "vendor_name",
            "customer_name",
            "issue_date",
            "due_date",
            "amount_net",
            "amount_tax",
            "amount_gross",
            "currency",
            "ai_summary",
            "ai_payload",
            "extraction_status",
            "extraction_error",
            "extracted_at",
            "updated_at",
        ]
    )
    return uploaded_invoice


def invoice_archive_summary(queryset) -> dict[str, Decimal | int]:
    income_total = queryset.filter(direction=UploadedInvoice.DIRECTION_OUTGOING).aggregate(total=models.Sum("amount_gross"))["total"] or Decimal("0.00")
    expense_total = queryset.filter(direction=UploadedInvoice.DIRECTION_INCOMING).aggregate(total=models.Sum("amount_gross"))["total"] or Decimal("0.00")
    open_total = queryset.filter(payment_status=UploadedInvoice.PAYMENT_OPEN).aggregate(total=models.Sum("amount_gross"))["total"] or Decimal("0.00")
    return {
        "income_total": _quantize_amount(income_total),
        "expense_total": _quantize_amount(expense_total),
        "open_total": _quantize_amount(open_total),
        "incoming_count": queryset.filter(direction=UploadedInvoice.DIRECTION_INCOMING).count(),
        "outgoing_count": queryset.filter(direction=UploadedInvoice.DIRECTION_OUTGOING).count(),
        "pending_count": queryset.filter(extraction_status__in=[UploadedInvoice.EXTRACTION_PENDING, UploadedInvoice.EXTRACTION_FAILED]).count(),
    }


def import_uploaded_invoices_from_directory(
    *,
    directory: Path,
    created_by=None,
    assigned_to=None,
    default_direction: str = UploadedInvoice.DIRECTION_INCOMING,
    analyze: bool = True,
) -> list[UploadedInvoice]:
    if not directory.exists():
        return []

    supported_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt"}
    imported: list[UploadedInvoice] = []
    for path in sorted(item for item in directory.iterdir() if item.is_file() and item.suffix.lower() in supported_suffixes):
        relative_name = path.name
        title = path.stem.replace("_", " ").replace("-", " ").strip() or path.stem
        uploaded_invoice, created = UploadedInvoice.objects.get_or_create(
            title=title,
            document=f"finance/invoices/{relative_name}",
            defaults={
                "direction": default_direction,
                "created_by": created_by,
                "assigned_to": assigned_to,
            },
        )
        if not created:
            imported.append(uploaded_invoice)
            continue
        target_dir = Path(settings.MEDIA_ROOT) / "finance" / "invoices"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / relative_name
        if not target_path.exists():
            target_path.write_bytes(path.read_bytes())
        uploaded_invoice.document.name = f"finance/invoices/{relative_name}"
        uploaded_invoice.created_by = created_by
        uploaded_invoice.assigned_to = assigned_to
        uploaded_invoice.direction = default_direction
        uploaded_invoice.save(update_fields=["document", "created_by", "assigned_to", "direction", "updated_at"])
        if analyze:
            analyze_uploaded_invoice(uploaded_invoice)
        imported.append(uploaded_invoice)
    return imported
