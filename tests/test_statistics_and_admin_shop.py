from decimal import Decimal
from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone


@pytest.fixture
def board_user(db):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="stats-board@example.com",
        password="StrongPass123!",
        first_name="Sina",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1987, 7, 7),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=202001,
        desired_join_date=date(2026, 4, 1),
        street_address="Ring 10",
        postal_code="04107",
        city="Leipzig",
        phone="+4915111223344",
        bank_name="GLS",
        account_holder_name="Sina Board",
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
        account_holder="Sina Board",
        mandate_reference="CSC-FIXTURE-STATS-BOARD",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


@pytest.mark.django_db
def test_board_navigation_contains_shop_and_statistics(client, board_user):
    client.force_login(board_user)

    response = client.get(reverse("core:dashboard"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert reverse("orders:shop") in html
    assert reverse("finance:statistics") in html


@pytest.mark.django_db
def test_finance_dashboard_payment_entries_link_to_invoice_detail(client, board_user, member_user):
    from apps.finance.models import Invoice, Payment

    invoice = Invoice.objects.create(
        profile=member_user.profile,
        invoice_number="INV-LINK-001",
        amount=Decimal("19.90"),
        due_date=member_user.profile.desired_join_date,
        status=Invoice.STATUS_OPEN,
    )
    Payment.objects.create(
        invoice=invoice,
        profile=member_user.profile,
        amount=Decimal("19.90"),
        method=Payment.METHOD_SEPA,
        status=Payment.STATUS_PENDING,
    )
    client.force_login(board_user)

    response = client.get(reverse("finance:dashboard"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert reverse("finance:invoice_detail", args=[invoice.id]) in html


@pytest.mark.django_db
def test_finance_statistics_page_renders_completed_order_data(client, board_user, member_user):
    from apps.inventory.models import Strain
    from apps.orders.models import Order, OrderItem

    flower = Strain.objects.create(
        name="Stats Flower",
        product_type=Strain.PRODUCT_TYPE_FLOWER,
        thc=Decimal("18.00"),
        cbd=Decimal("0.20"),
        price=Decimal("8.50"),
        stock=Decimal("100.00"),
    )
    order = Order.objects.create(
        member=member_user,
        status=Order.STATUS_COMPLETED,
        total=Decimal("17.00"),
        total_grams=Decimal("2.00"),
        reserved_until=timezone.now(),
    )
    OrderItem.objects.create(
        order=order,
        strain=flower,
        quantity_grams=Decimal("2.00"),
        unit_price=Decimal("8.50"),
        total_price=Decimal("17.00"),
    )
    client.force_login(board_user)

    response = client.get(reverse("finance:statistics"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "Stats Flower" in html
    assert "Blueten gesamt" in html


@pytest.mark.django_db
def test_finance_statistics_csv_export_contains_month_rows(client, board_user, member_user):
    from apps.inventory.models import Strain
    from apps.orders.models import Order, OrderItem

    cutting = Strain.objects.create(
        name="Stats Cutting",
        product_type=Strain.PRODUCT_TYPE_CUTTING,
        thc=Decimal("0.00"),
        cbd=Decimal("0.00"),
        price=Decimal("4.50"),
        stock=Decimal("50.00"),
    )
    order = Order.objects.create(
        member=member_user,
        status=Order.STATUS_COMPLETED,
        total=Decimal("9.00"),
        reserved_until=timezone.now(),
    )
    OrderItem.objects.create(
        order=order,
        strain=cutting,
        quantity_grams=Decimal("2.00"),
        unit_price=Decimal("4.50"),
        total_price=Decimal("9.00"),
    )
    client.force_login(board_user)

    response = client.get(reverse("finance:statistics") + "?format=csv")

    content = response.content.decode("utf-8")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert "Stats Cutting" in content
    assert "Top-Produkte" in content


@pytest.mark.django_db
def test_finance_statistics_page_shows_year_comparison_and_split_lists(client, board_user, member_user):
    from apps.inventory.models import Strain
    from apps.orders.models import Order, OrderItem

    flower = Strain.objects.create(
        name="Compare Flower",
        product_type=Strain.PRODUCT_TYPE_FLOWER,
        thc=Decimal("19.00"),
        cbd=Decimal("0.10"),
        price=Decimal("9.50"),
        stock=Decimal("100.00"),
    )
    cutting = Strain.objects.create(
        name="Compare Cutting",
        product_type=Strain.PRODUCT_TYPE_CUTTING,
        thc=Decimal("0.00"),
        cbd=Decimal("0.00"),
        price=Decimal("5.00"),
        stock=Decimal("40.00"),
    )
    current_order = Order.objects.create(
        member=member_user,
        status=Order.STATUS_COMPLETED,
        total=Decimal("19.00"),
        reserved_until=timezone.now(),
    )
    previous_order = Order.objects.create(
        member=member_user,
        status=Order.STATUS_COMPLETED,
        total=Decimal("5.00"),
        reserved_until=timezone.now(),
    )
    current_order.updated_at = timezone.now()
    current_order.save(update_fields=["updated_at"])
    previous_order.updated_at = timezone.now().replace(year=timezone.now().year - 1)
    previous_order.save(update_fields=["updated_at"])
    OrderItem.objects.create(
        order=current_order,
        strain=flower,
        quantity_grams=Decimal("2.00"),
        unit_price=Decimal("9.50"),
        total_price=Decimal("19.00"),
    )
    OrderItem.objects.create(
        order=previous_order,
        strain=cutting,
        quantity_grams=Decimal("1.00"),
        unit_price=Decimal("5.00"),
        total_price=Decimal("5.00"),
    )
    client.force_login(board_user)

    response = client.get(reverse("finance:statistics") + f"?year={timezone.now().year}")

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "Jahresvergleich" in html
    assert "Top-Sorten nach Gramm" in html
    assert "Top-Sorten nach Stueck" in html
