from datetime import timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.test import override_settings
from django.utils import timezone


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_sepa_prenotification_and_collection(member_user):
    from apps.finance.models import Invoice
    from apps.finance.services import (
        collect_due_sepa_payments,
        create_sepa_mandate,
        schedule_sepa_payment,
        send_sepa_prenotifications,
    )

    profile = member_user.profile
    create_sepa_mandate(
        user=member_user,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Max Mustermann",
    )

    invoice = Invoice.objects.create(
        profile=profile,
        invoice_number="INV-TEST-001",
        amount=Decimal("49.90"),
        due_date=timezone.localdate(),
        status=Invoice.STATUS_OPEN,
    )

    payment = schedule_sepa_payment(invoice=invoice, scheduled_for=timezone.localdate() + timedelta(days=1))
    assert payment is not None

    sent = send_sepa_prenotifications(today=timezone.localdate())
    assert sent == 1
    assert len(mail.outbox) == 1

    payment.refresh_from_db()
    assert payment.status == payment.STATUS_PRNOTIFIED

    payment.scheduled_for = timezone.localdate()
    payment.save(update_fields=["scheduled_for"])

    collected = collect_due_sepa_payments(today=timezone.localdate())
    assert collected == 1

    payment.refresh_from_db()
    invoice.refresh_from_db()
    assert payment.status == payment.STATUS_COLLECTED
    assert invoice.status == Invoice.STATUS_PAID


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_reminder_levels_1_and_2_with_fee(member_user):
    from apps.finance.models import Invoice
    from apps.finance.services import send_due_reminders

    due_date = timezone.localdate() - timedelta(days=14)
    invoice = Invoice.objects.create(
        profile=member_user.profile,
        invoice_number="INV-TEST-REM-1",
        amount=Decimal("30.00"),
        due_date=due_date,
        status=Invoice.STATUS_OPEN,
    )

    sent_l1 = send_due_reminders(today=due_date + timedelta(days=7))
    assert sent_l1 == 1
    invoice.refresh_from_db()
    assert invoice.reminder_level == 1
    assert invoice.amount == Decimal("30.00")

    sent_l2 = send_due_reminders(today=due_date + timedelta(days=14))
    assert sent_l2 == 1
    invoice.refresh_from_db()
    assert invoice.reminder_level == 2
    assert invoice.amount == Decimal("35.00")


@pytest.mark.django_db
def test_generate_datev_export_file(member_user):
    from apps.finance.models import Invoice
    from apps.finance.services import generate_datev_export

    invoice = Invoice.objects.create(
        profile=member_user.profile,
        invoice_number="INV-TEST-DATEV-1",
        amount=Decimal("88.00"),
        due_date=timezone.localdate(),
        status=Invoice.STATUS_OPEN,
    )

    output = generate_datev_export(period="month", anchor=timezone.localdate())

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "Belegdatum;Belegnummer;Konto;Gegenkonto;Betrag;Buchungstext;Mitglied;Status" in content
    assert invoice.invoice_number in content
