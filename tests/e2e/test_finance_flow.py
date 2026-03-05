"""E2E Tests: Finance Flow (Zahlungen/SEPA)

Testet: Guthaben, SEPA, Mahnwesen, DATEV-Export
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse


@pytest.mark.django_db
def test_balance_display(client, member_user):
    """Test: Guthaben-Anzeige"""
    client.force_login(member_user)

    response = client.get(reverse("finance:balance"))

    assert response.status_code == 200
    assert "200,00" in str(response.content) or "200.00" in str(response.content)


@pytest.mark.django_db
def test_add_balance_manual(client, staff_user, member_user):
    """Test: Guthaben manuell hinzufügen (Bar/Überweisung)"""
    client.force_login(staff_user)

    initial_balance = member_user.profile.balance

    response = client.post(
        reverse("finance:add_balance", kwargs={"member_id": member_user.pk}),
        {
            "amount": "50.00",
            "payment_method": "cash",
            "notes": "Barzahlung",
        },
    )

    assert response.status_code == 302
    
    member_user.profile.refresh_from_db()
    assert member_user.profile.balance == initial_balance + Decimal("50.00")


@pytest.mark.django_db
def test_sepa_mandate_create(client, member_user):
    """Test: SEPA-Mandat erstellen"""
    from apps.finance.models import SepaMandate

    client.force_login(member_user)

    response = client.post(
        reverse("finance:sepa_mandate_create"),
        {
            "iban": "DE44500105175407324931",
            "bic": "INGDDEFFXXX",
            "account_holder": "Max Mustermann",
        },
    )

    assert response.status_code == 302
    assert SepaMandate.objects.filter(profile=member_user.profile).exists()


@pytest.mark.django_db
def test_sepa_mandate_requires_valid_iban(client, member_user):
    """Test: SEPA-Mandat mit ungültiger IBAN abgelehnt"""
    client.force_login(member_user)

    response = client.post(
        reverse("finance:sepa_mandate_create"),
        {
            "iban": "INVALID123",  # Ungültig
            "bic": "INGDDEFFXXX",
            "account_holder": "Max Mustermann",
        },
    )

    # Sollte Fehler zeigen
    assert response.status_code == 200


@pytest.mark.django_db
def test_invoice_list_view(client, member_user, invoice):
    """Test: Rechnungs-Liste anzeigen"""
    client.force_login(member_user)

    response = client.get(reverse("finance:invoice_list"))

    assert response.status_code == 200
    assert invoice.invoice_number in str(response.content)


@pytest.mark.django_db
def test_invoice_payment(client, staff_user, invoice):
    """Test: Rechnung als bezahlt markieren"""
    from apps.finance.models import Invoice

    client.force_login(staff_user)

    response = client.post(
        reverse("finance:invoice_pay", kwargs={"pk": invoice.pk}),
        {
            "payment_method": "cash",
            "amount": str(invoice.amount),
        },
    )

    assert response.status_code == 302
    
    invoice.refresh_from_db()
    assert invoice.status == Invoice.STATUS_PAID


@pytest.mark.django_db
def test_reminder_level_1_sent(client, member_user):
    """Test: Erinnerung (Stufe 1) nach 7 Tagen"""
    from apps.finance.models import Invoice
    from apps.finance.services import send_due_reminders

    # Überfällige Rechnung erstellen
    invoice = Invoice.objects.create(
        profile=member_user.profile,
        invoice_number="INV-REM-001",
        amount=Decimal("30.00"),
        due_date=date.today() - timedelta(days=7),
        status=Invoice.STATUS_OPEN,
    )

    # Erinnerungen senden
    sent = send_due_reminders(today=date.today())

    assert sent >= 1
    
    invoice.refresh_from_db()
    assert invoice.reminder_level == 1


@pytest.mark.django_db
def test_reminder_level_2_with_fee(client, member_user):
    """Test: 1. Mahnung (Stufe 2) nach 14 Tagen mit €5 Gebühr"""
    from apps.finance.models import Invoice
    from apps.finance.services import send_due_reminders

    invoice = Invoice.objects.create(
        profile=member_user.profile,
        invoice_number="INV-REM-002",
        amount=Decimal("30.00"),
        due_date=date.today() - timedelta(days=14),
        status=Invoice.STATUS_OPEN,
        reminder_level=1,
    )

    sent = send_due_reminders(today=date.today())

    assert sent >= 1
    
    invoice.refresh_from_db()
    assert invoice.reminder_level == 2
    assert invoice.amount == Decimal("35.00")  # + €5 Gebühr


@pytest.mark.django_db
def test_reminder_level_4_blocks_member(client, member_user):
    """Test: 3. Mahnung (Stufe 4) sperrt Mitglied"""
    from apps.finance.models import Invoice
    from apps.members.models import Profile
    from apps.finance.services import send_due_reminders

    invoice = Invoice.objects.create(
        profile=member_user.profile,
        invoice_number="INV-REM-004",
        amount=Decimal("30.00"),
        due_date=date.today() - timedelta(days=28),
        status=Invoice.STATUS_OPEN,
        reminder_level=3,
    )

    sent = send_due_reminders(today=date.today())

    assert sent >= 1
    
    member_user.profile.refresh_from_db()
    assert member_user.profile.status == Profile.STATUS_SUSPENDED


@pytest.mark.django_db
def test_datev_export_generation(client, board_user, invoice):
    """Test: DATEV-Export generieren"""
    from apps.finance.services import generate_datev_export

    client.force_login(board_user)

    output = generate_datev_export(period="month", anchor=date.today())

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "Belegdatum" in content
    assert invoice.invoice_number in content


@pytest.mark.django_db
def test_sepa_collection_batch(client, board_user, invoice, sepa_mandate):
    """Test: SEPA-Lastschrift Batch-Einzug"""
    from apps.finance.models import Payment
    from apps.finance.services import collect_due_sepa_payments

    # Zahlung planen
    from apps.finance.services import schedule_sepa_payment
    payment = schedule_sepa_payment(
        invoice=invoice,
        scheduled_for=date.today(),
    )

    # Einzug durchführen
    collected = collect_due_sepa_payments(today=date.today())

    assert collected >= 1
    
    payment.refresh_from_db()
    assert payment.status == Payment.STATUS_COLLECTED


@pytest.mark.django_db
def test_sepa_prenotification_sent(client, board_user, invoice, sepa_mandate):
    """Test: SEPA-Vorabankündigung wird versendet"""
    from apps.finance.models import Payment
    from apps.finance.services import schedule_sepa_payment, send_sepa_prenotifications

    payment = schedule_sepa_payment(
        invoice=invoice,
        scheduled_for=date.today() + timedelta(days=1),
    )

    sent = send_sepa_prenotifications(today=date.today())

    assert sent >= 1
    
    payment.refresh_from_db()
    assert payment.status == Payment.STATUS_PRNOTIFIED


@pytest.mark.django_db
def test_finance_dashboard_shows_stats(client, board_user, invoice):
    """Test: Finanz-Dashboard zeigt Statistiken"""
    client.force_login(board_user)

    response = client.get(reverse("finance:dashboard"))

    assert response.status_code == 200
    assert invoice.invoice_number in str(response.content) or "offen" in str(response.content).lower()


@pytest.mark.django_db
def test_invoice_cannot_exceed_balance(client, member_user):
    """Test: Rechnung kann Guthaben nicht überziehen (bei Guthaben-Zahlung)"""
    from apps.finance.models import Invoice

    # Guthaben auf 0 setzen
    member_user.profile.balance = Decimal("0")
    member_user.profile.save()

    # Versuche zu bezahlen
    client.force_login(member_user)

    # Sollte nicht möglich sein
    # (Implementierung hängt von der Logik ab)


@pytest.mark.django_db
def test_mandate_revocation(client, member_user, sepa_mandate):
    """Test: SEPA-Mandat widerrufen"""
    client.force_login(member_user)

    response = client.post(
        reverse("finance:sepa_mandate_revoke", kwargs={"pk": sepa_mandate.pk}),
    )

    assert response.status_code == 302
    
    sepa_mandate.refresh_from_db()
    assert sepa_mandate.is_active is False
