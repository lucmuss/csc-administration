from __future__ import annotations

import io
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.http import Http404
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.finance.models import BalanceTopUp, Invoice, UploadedInvoice
from apps.members.models import Profile


@pytest.fixture
def board_user(db):
    user = get_user_model().objects.create_user(
        email="finance-board@example.com",
        password="StrongPass123!",
        first_name="Fin",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1988, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    return user


@pytest.mark.django_db
def test_finance_dashboard_member_access(client, member_user):
    client.force_login(member_user)
    response = client.get(reverse("finance:dashboard"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_stripe_method_create_member_redirects_to_checkout(client, member_user, monkeypatch):
    client.force_login(member_user)
    monkeypatch.setattr(
        "apps.finance.views.create_stripe_setup_session_for_member",
        lambda **kwargs: "https://checkout.example/session",
    )
    response = client.get(reverse("finance:stripe_method_create"))
    assert response.status_code == 302
    assert response.url == "https://checkout.example/session"


@pytest.mark.django_db
def test_stripe_method_create_board_gets_404(client, board_user):
    client.force_login(board_user)
    response = client.get(reverse("finance:stripe_method_create"))
    assert response.status_code == 404


@pytest.mark.django_db
def test_invoice_detail_member_cannot_access_foreign_invoice(client, member_user, board_user):
    foreign = get_user_model().objects.create_user(
        email="other-finance@example.com",
        password="StrongPass123!",
        first_name="Other",
        last_name="Member",
        role=User.ROLE_MEMBER,
    )
    foreign_profile = Profile.objects.create(
        user=foreign,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    invoice = Invoice.objects.create(
        profile=foreign_profile,
        invoice_number="INV-FOREIGN-1",
        amount=Decimal("20.00"),
        due_date=timezone.localdate(),
        status=Invoice.STATUS_OPEN,
    )

    client.force_login(member_user)
    response = client.get(reverse("finance:invoice_detail", args=[invoice.id]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_invoice_pdf_response_for_owner(client, member_user, monkeypatch):
    invoice = Invoice.objects.create(
        profile=member_user.profile,
        invoice_number="INV-OWN-1",
        amount=Decimal("15.00"),
        due_date=timezone.localdate(),
        status=Invoice.STATUS_OPEN,
    )
    monkeypatch.setattr("apps.finance.views.render_invoice_pdf", lambda inv: b"%PDF-1.4\n")

    client.force_login(member_user)
    response = client.get(reverse("finance:invoice_pdf", args=[invoice.id]))
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_invoice_pdf_requires_login_redirects_to_login(client, member_user):
    invoice = Invoice.objects.create(
        profile=member_user.profile,
        invoice_number="INV-LOGIN-REQ-1",
        amount=Decimal("19.00"),
        due_date=timezone.localdate(),
        status=Invoice.STATUS_OPEN,
    )

    response = client.get(reverse("finance:invoice_pdf", args=[invoice.id]))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_topup_success_unknown_topup_redirects_dashboard(client, member_user):
    client.force_login(member_user)
    response = client.get(reverse("finance:topup_success"), {"topup_id": "9999", "session_id": "cs_x"})
    assert response.status_code == 302
    assert response.url == reverse("finance:dashboard")


@pytest.mark.django_db
def test_archive_requires_board_or_staff(client, member_user):
    client.force_login(member_user)
    response = client.get(reverse("finance:archive"))
    assert response.status_code == 404


@pytest.mark.django_db
def test_archive_board_uploads_and_redirects_detail(client, board_user, monkeypatch):
    client.force_login(board_user)
    monkeypatch.setattr("apps.finance.views.analyze_uploaded_invoice", lambda invoice: invoice)
    upload = SimpleUploadedFile("invoice.txt", b"hello", content_type="text/plain")

    response = client.post(
        reverse("finance:archive"),
        data={"direction": "incoming", "document": upload, "payment_status": "open", "notes": ""},
        follow=False,
    )
    assert response.status_code == 302
    assert "/finance/archive/" in response.url


@pytest.mark.django_db
def test_statistics_csv_export_for_board(client, board_user):
    client.force_login(board_user)
    response = client.get(reverse("finance:statistics") + "?format=csv")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
