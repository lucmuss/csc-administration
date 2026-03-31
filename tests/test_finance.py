from datetime import timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
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


@pytest.mark.django_db
def test_balance_transactions_update_profile_balance(member_user):
    from apps.finance.models import BalanceTransaction
    from apps.finance.services import add_balance_transaction, balance_breakdown

    add_balance_transaction(
        profile=member_user.profile,
        amount=Decimal("24.00"),
        kind=BalanceTransaction.KIND_MEMBERSHIP_FEE,
        note="Mitgliedsbeitrag April",
        reference="membership-april",
    )
    add_balance_transaction(
        profile=member_user.profile,
        amount=Decimal("100.00"),
        kind=BalanceTransaction.KIND_TOPUP,
        note="Top-up",
        reference="topup-april",
    )

    member_user.profile.refresh_from_db()
    breakdown = balance_breakdown(member_user.profile)
    assert member_user.profile.balance == Decimal("324.00")
    assert breakdown["membership_contributions"] == Decimal("24.00")
    assert breakdown["topups"] == Decimal("100.00")


@pytest.mark.django_db
def test_member_finance_dashboard_shows_balance_section(client, member_user):
    client.force_login(member_user)

    response = client.get(reverse("finance:dashboard"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Gesamtguthaben" in content
    assert "Mit Stripe aufladen" in content
    assert "Schnellauswahl" in content


@pytest.mark.django_db
def test_topup_form_supports_preset_amounts():
    from apps.finance.forms import BalanceTopUpForm

    form = BalanceTopUpForm(data={"preset_amount": "50.00", "amount": ""})

    assert form.is_valid()
    assert form.cleaned_data["final_amount"] == Decimal("50.00")


@pytest.mark.django_db
def test_topup_form_rejects_negative_custom_amount():
    from apps.finance.forms import BalanceTopUpForm

    form = BalanceTopUpForm(data={"preset_amount": "custom", "amount": "-50"})

    assert not form.is_valid()
    assert "amount" in form.errors or "__all__" in form.errors


@pytest.mark.django_db
def test_mandate_form_prefills_existing_sepa_data(client, member_user):
    client.force_login(member_user)

    response = client.get(reverse("finance:mandate_create"))

    content = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "DE44500105175407324931" in content
    assert "INGDDEFFXXX" in content
    assert "Max Mustermann" in content


@pytest.mark.django_db
def test_posting_mandate_requires_confirmation_step(client, member_user):
    client.force_login(member_user)

    response = client.post(
        reverse("finance:mandate_create"),
        data={
            "iban": "DE02100100109307118603",
            "bic": "PBNKDEFF",
            "account_holder": "Max Muster Neu",
        },
    )

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "SEPA-Mandat bestaetigen" in html
    assert "DE02100100109307118603" in html


@pytest.mark.django_db
def test_confirming_mandate_updates_existing_sepa_record(client, member_user):
    from apps.finance.models import SepaMandate

    existing_id = member_user.profile.sepa_mandate.id
    client.force_login(member_user)

    response = client.post(
        reverse("finance:mandate_create"),
        data={
            "iban": "DE02100100109307118603",
            "bic": "PBNKDEFF",
            "account_holder": "Max Muster Neu",
            "confirm": "yes",
        },
    )

    member_user.profile.refresh_from_db()
    mandate = SepaMandate.objects.get(id=existing_id)
    assert response.status_code == 302
    assert member_user.profile.sepa_mandate_id == existing_id
    assert mandate.iban == "DE02100100109307118603"
    assert mandate.bic == "PBNKDEFF"
    assert mandate.account_holder == "Max Muster Neu"


@pytest.mark.django_db
@override_settings(MEMBER_MONTHLY_FEE="24.00")
def test_apply_monthly_membership_credits_is_idempotent(member_user):
    from apps.finance.models import BalanceTransaction
    from apps.finance.services import apply_monthly_membership_credits

    credited_first = apply_monthly_membership_credits(today=timezone.localdate())
    credited_second = apply_monthly_membership_credits(today=timezone.localdate())

    member_user.profile.refresh_from_db()
    entries = BalanceTransaction.objects.filter(
        profile=member_user.profile,
        kind=BalanceTransaction.KIND_MEMBERSHIP_FEE,
    )
    assert credited_first >= 1
    assert credited_second == 0
    assert entries.count() == 1
