from datetime import date
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone


@pytest.fixture
def board_user(db):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="roles-board@example.com",
        password="StrongPass123!",
        first_name="Rike",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1989, 6, 6),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=101700,
        desired_join_date=date(2026, 4, 1),
        street_address="Teststrasse 7",
        postal_code="04107",
        city="Leipzig",
        phone="+4917612345678",
        bank_name="GLS",
        account_holder_name="Rike Board",
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
        account_holder="Rike Board",
        mandate_reference="CSC-FIXTURE-ROLE-BOARD",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


@pytest.mark.django_db
def test_board_can_promote_member_to_staff(client, board_user, member_user):
    client.force_login(board_user)

    response = client.post(
        reverse("members:action", args=[member_user.profile.id]),
        {"action": "promote_staff", "confirm": "yes"},
    )

    member_user.refresh_from_db()
    assert response.status_code == 302
    assert member_user.role == member_user.ROLE_STAFF
    assert member_user.is_staff is True


@pytest.mark.django_db
def test_member_dashboard_no_longer_links_to_members_admin(client, member_user):
    client.force_login(member_user)

    response = client.get(reverse("core:dashboard"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert '>Mitglieder</a>' not in html
    redirect_response = client.get(reverse("members:directory"))
    assert redirect_response.status_code == 302
    assert redirect_response.url == reverse("core:dashboard")


@pytest.mark.django_db
def test_shop_supports_accessory_filter_and_custom_quantity(client, member_user):
    from apps.inventory.models import Strain

    accessory = Strain.objects.create(
        name="Aktivkohlefilter 50er",
        product_type=Strain.PRODUCT_TYPE_ACCESSORY,
        thc=Decimal("0.00"),
        cbd=Decimal("0.00"),
        price=Decimal("4.50"),
        stock=Decimal("25.00"),
    )
    flower = Strain.objects.create(
        name="Custom Flower",
        product_type=Strain.PRODUCT_TYPE_FLOWER,
        thc=Decimal("18.00"),
        cbd=Decimal("0.40"),
        price=Decimal("8.00"),
        stock=Decimal("50.00"),
    )
    client.force_login(member_user)

    filter_response = client.get(reverse("orders:shop") + "?type=accessory")
    flower_response = client.get(reverse("orders:shop") + "?type=flower")
    add_response = client.post(
        reverse("orders:add_to_cart"),
        {"strain_id": flower.id, "quantity": "custom", "custom_quantity": "16"},
    )

    html = filter_response.content.decode("utf-8")
    assert filter_response.status_code == 200
    assert accessory.name in html
    assert "Eigene Menge" in flower_response.content.decode("utf-8")
    assert add_response.status_code == 302
    assert client.session["cart"][str(flower.id)] == "16"


@pytest.mark.django_db
def test_board_can_upload_invoice_archive_entry(client, board_user, settings):
    from apps.finance.models import UploadedInvoice

    client.force_login(board_user)
    settings.OPENROUTER_API_KEY = ""
    upload = SimpleUploadedFile("invoice.txt", b"Rechnung 123\nGesamt 49,90 EUR", content_type="text/plain")

    response = client.post(
        reverse("finance:archive"),
        {
            "title": "Strom April",
            "direction": "incoming",
            "payment_status": "open",
            "assigned_to": board_user.id,
            "notes": "Bitte pruefen",
            "document": upload,
        },
    )

    invoice = UploadedInvoice.objects.get(title="Strom April")
    assert response.status_code == 302
    assert invoice.assigned_to == board_user
    assert invoice.extraction_status in {
        UploadedInvoice.EXTRACTION_FAILED,
        UploadedInvoice.EXTRACTION_PENDING,
        UploadedInvoice.EXTRACTION_SUCCESS,
    }


@pytest.mark.django_db
def test_board_can_upload_invoice_without_manual_title(client, board_user, settings):
    from apps.finance.models import UploadedInvoice

    client.force_login(board_user)
    settings.OPENROUTER_API_KEY = ""
    upload = SimpleUploadedFile("strom_april_2026.txt", b"Rechnung 4711\nGesamt 49,90 EUR", content_type="text/plain")

    response = client.post(
        reverse("finance:archive"),
        {
            "title": "",
            "direction": "incoming",
            "payment_status": "open",
            "assigned_to": board_user.id,
            "notes": "",
            "document": upload,
        },
    )

    invoice = UploadedInvoice.objects.latest("id")
    assert response.status_code == 302
    assert invoice.title
    assert "strom" in invoice.title.lower()


@pytest.mark.django_db
def test_archive_list_links_title_to_detail_view(client, board_user):
    from apps.finance.models import UploadedInvoice

    UploadedInvoice.objects.create(
        title="Miete April",
        direction="incoming",
        payment_status="open",
        created_by=board_user,
        document=SimpleUploadedFile("miete.txt", b"Rechnung", content_type="text/plain"),
    )
    client.force_login(board_user)

    response = client.get(reverse("finance:archive"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert reverse("finance:archive_detail", args=[UploadedInvoice.objects.latest("id").id]) in html
