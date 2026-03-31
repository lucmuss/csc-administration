from datetime import date
from decimal import Decimal

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone


@pytest.fixture
def board_user(db):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="board@example.com",
        password="StrongPass123!",
        first_name="Bea",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1985, 5, 5),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100001,
        desired_join_date=date(2026, 4, 1),
        street_address="Karl-Liebknecht-Strasse 9",
        postal_code="04107",
        city="Leipzig",
        phone="+4915112345678",
        bank_name="GLS",
        account_holder_name="Bea Board",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        registration_completed_at=timezone.now(),
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE12500105170648489890",
        bic="GENODEM1GLS",
        account_holder="Bea Board",
        mandate_reference="CSC-FIXTURE-BOARD",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


@pytest.fixture
def pending_user(db):
    from apps.accounts.models import User
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="pending@example.com",
        password="StrongPass123!",
        first_name="Pia",
        last_name="Pending",
        role=User.ROLE_MEMBER,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1993, 3, 3),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    return user


@pytest.fixture
def stock_strain(db):
    from apps.inventory.models import Strain

    return Strain.objects.create(
        name="Orange Bud",
        thc=Decimal("20.00"),
        cbd=Decimal("0.50"),
        price=Decimal("8.00"),
        stock=Decimal("50.00"),
    )


@pytest.mark.django_db
def test_board_can_open_admin_order_list(client, board_user, member_user, stock_strain):
    from apps.orders.services import CartLine, create_reserved_order

    create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=stock_strain.id, quantity=Decimal("2.00"))])

    client.force_login(board_user)
    response = client.get(reverse("orders:admin_list"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "Bestellungen" in html
    assert member_user.email in html
    assert "Ausgeben & abbuchen" in html


@pytest.mark.django_db
def test_board_can_complete_reserved_order(client, board_user, member_user, stock_strain):
    from apps.members.models import Profile
    from apps.orders.models import Order
    from apps.orders.services import CartLine, create_reserved_order

    order = create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=stock_strain.id, quantity=Decimal("2.00"))])
    profile = Profile.objects.get(user=member_user)
    assert profile.balance == Decimal("224.00")

    client.force_login(board_user)
    confirm_response = client.post(reverse("orders:admin_action", args=[order.id]), {"action": "complete"})
    assert confirm_response.status_code == 200
    assert "Bitte bestaetige diese Aktion." in confirm_response.content.decode("utf-8")

    response = client.post(reverse("orders:admin_action", args=[order.id]), {"action": "complete", "confirm": "yes"})

    order.refresh_from_db()
    profile.refresh_from_db()
    assert response.status_code == 302
    assert order.status == Order.STATUS_COMPLETED
    assert order.paid_with_balance == Decimal("16.00")
    assert profile.balance == Decimal("208.00")


@pytest.mark.django_db
def test_board_can_cancel_reserved_order_and_restore_stock(client, board_user, member_user, stock_strain):
    from apps.members.models import Profile
    from apps.orders.models import Order
    from apps.orders.services import CartLine, create_reserved_order

    order = create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=stock_strain.id, quantity=Decimal("2.00"))])

    client.force_login(board_user)
    confirm_response = client.post(reverse("orders:admin_action", args=[order.id]), {"action": "cancel"})
    assert confirm_response.status_code == 200
    assert "Bitte bestaetige diese Aktion." in confirm_response.content.decode("utf-8")

    response = client.post(reverse("orders:admin_action", args=[order.id]), {"action": "cancel", "confirm": "yes"})

    order.refresh_from_db()
    stock_strain.refresh_from_db()
    profile = Profile.objects.get(user=member_user)
    assert response.status_code == 302
    assert order.status == Order.STATUS_CANCELLED
    assert stock_strain.stock == Decimal("50.00")
    assert profile.balance == Decimal("224.00")


@pytest.mark.django_db
def test_board_can_open_member_detail_with_order_history(client, board_user, member_user, stock_strain):
    from apps.orders.services import CartLine, create_reserved_order

    create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=stock_strain.id, quantity=Decimal("2.00"))])

    client.force_login(board_user)
    response = client.get(reverse("members:detail", args=[member_user.profile.id]))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert member_user.email in html
    assert "Historie und Reservierungen" in html
    assert "Orange Bud" in html


@pytest.mark.django_db
def test_member_order_detail_and_invoice_detail_are_clickable(client, member_user, stock_strain):
    from apps.orders.services import CartLine, create_reserved_order

    order = create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=stock_strain.id, quantity=Decimal("2.00"))])

    client.force_login(member_user)

    order_response = client.get(reverse("orders:detail", args=[order.id]))
    invoice_response = client.get(reverse("finance:invoice_detail", args=[order.invoice.id]))
    pdf_response = client.get(reverse("finance:invoice_pdf", args=[order.invoice.id]))

    assert order_response.status_code == 200
    assert "Was in der Bestellung enthalten ist" in order_response.content.decode("utf-8")
    assert invoice_response.status_code == 200
    assert order.invoice.invoice_number in invoice_response.content.decode("utf-8")
    assert pdf_response.status_code == 200
    assert pdf_response["Content-Type"] == "application/pdf"


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_verify_member_sends_status_email(client, board_user, pending_user):
    from apps.messaging.models import EmailGroupMember

    client.force_login(board_user)

    confirm_response = client.post(reverse("members:action", args=[pending_user.profile.id]), {"action": "verify"})
    assert confirm_response.status_code == 200
    assert "Bitte bestaetige diese Aktion." in confirm_response.content.decode("utf-8")

    response = client.post(reverse("members:action", args=[pending_user.profile.id]), {"action": "verify", "confirm": "yes"})

    pending_user.profile.refresh_from_db()
    assert response.status_code == 302
    assert pending_user.profile.is_verified is True
    assert len(mail.outbox) == 1
    assert pending_user.email in mail.outbox[0].to
    assert "Mitgliedschaft freigeschaltet" in mail.outbox[0].subject
    assert EmailGroupMember.objects.filter(group__name="Wichtige Vereinsinfos", member=pending_user.profile).exists() is True


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_activate_member_adds_required_and_optional_email_groups(client, board_user, pending_user):
    from apps.messaging.models import EmailGroupMember

    pending_user.profile.optional_newsletter_opt_in = True
    pending_user.profile.save(update_fields=["optional_newsletter_opt_in", "updated_at"])
    client.force_login(board_user)

    response = client.post(reverse("members:action", args=[pending_user.profile.id]), {"action": "activate", "confirm": "yes"})

    pending_user.profile.refresh_from_db()
    assert response.status_code == 302
    assert EmailGroupMember.objects.filter(group__name="Wichtige Vereinsinfos", member=pending_user.profile).exists() is True
    assert EmailGroupMember.objects.filter(group__name="Preislisten und Angebote", member=pending_user.profile).exists() is True


@pytest.mark.django_db
def test_delete_member_redirects_back_to_directory(client, board_user, pending_user):
    client.force_login(board_user)

    response = client.post(reverse("members:action", args=[pending_user.profile.id]), {"action": "delete_member", "confirm": "yes"})

    assert response.status_code == 302
    assert response.url == reverse("members:directory")


@pytest.mark.django_db
def test_invoice_list_pdf_link_opens_in_new_tab(client, member_user, stock_strain):
    from apps.orders.services import CartLine, create_reserved_order

    order = create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=stock_strain.id, quantity=Decimal("1.00"))])
    client.force_login(member_user)

    response = client.get(reverse("finance:invoice_list"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert reverse("finance:invoice_pdf", args=[order.invoice.id]) in html
    assert 'target="_blank"' in html


@pytest.mark.django_db
def test_board_dashboard_cards_link_to_admin_sections(client, board_user):
    client.force_login(board_user)
    response = client.get(reverse("core:dashboard"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert 'href="/members/admin/"' in html
    assert 'href="/orders/admin/?status=reserved"' in html
    assert 'href="/compliance/suspicious-activities/"' in html


@pytest.mark.django_db
def test_member_directory_hides_sensitive_admin_finance_fields(client, member_user):
    client.force_login(member_user)
    response = client.get(reverse("members:directory"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "Aktive Mitglieder und Profile im Verein auf einen Blick." in html
    assert "offene Rechnungen" not in html
    assert "CSV-Export" not in html


@pytest.mark.django_db
def test_member_directory_normalizes_unsafe_search_query(client, member_user):
    client.force_login(member_user)

    response = client.get(reverse("members:directory"), {"q": "<script>alert('x')</script>"})

    assert response.status_code == 302
    assert "<" not in response["Location"]
    assert "scriptalertxscript" in response["Location"]
