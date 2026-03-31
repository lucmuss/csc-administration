from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone


@pytest.fixture
def board_user(db):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="ops-board@example.com",
        password="StrongPass123!",
        first_name="Olaf",
        last_name="Vorstand",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100010,
        desired_join_date=date(2026, 4, 1),
        street_address="Karl-Liebknecht-Strasse 9",
        postal_code="04107",
        city="Leipzig",
        phone="+4915112345678",
        bank_name="ING",
        account_holder_name="Olaf Vorstand",
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
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Olaf Vorstand",
        mandate_reference="CSC-FIXTURE-OPS-BOARD",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


@pytest.mark.django_db
def test_inventory_strain_pages_use_app_routes(client, board_user):
    client.force_login(board_user)

    list_response = client.get(reverse("inventory:strain_list"))
    create_response = client.get(reverse("inventory:strain_create"))

    assert list_response.status_code == 200
    assert create_response.status_code == 200
    content = list_response.content.decode()
    assert reverse("inventory:strain_create") in content
    assert "/admin/inventory/strain/add/" not in content
    assert "Produktarten, Preise, Bilder, Bestand und Aktiv-Status verwaltest du jetzt direkt hier in der App." in content


@pytest.mark.django_db
def test_inventory_location_pages_use_app_routes(client, board_user):
    from apps.inventory.models import InventoryLocation

    location = InventoryLocation.objects.create(name="Hauptlager", type=InventoryLocation.TYPE_VAULT, capacity=Decimal("250.00"))
    client.force_login(board_user)

    list_response = client.get(reverse("inventory:location_list"))
    create_response = client.get(reverse("inventory:location_create"))
    edit_response = client.get(reverse("inventory:location_edit", args=[location.id]))

    assert list_response.status_code == 200
    assert create_response.status_code == 200
    assert edit_response.status_code == 200
    html = list_response.content.decode()
    assert reverse("inventory:location_create") in html
    assert reverse("inventory:location_edit", args=[location.id]) in html
    assert "/admin/inventory/inventorylocation/add/" not in html


@pytest.mark.django_db
def test_inventory_count_rejects_decimal_values(client, board_user):
    from apps.inventory.models import InventoryItem, InventoryLocation, Strain

    strain = Strain.objects.create(
        name="Test Bluete",
        product_type=Strain.PRODUCT_TYPE_FLOWER,
        thc=Decimal("18.00"),
        cbd=Decimal("0.20"),
        price=Decimal("8.00"),
        stock=Decimal("10.00"),
    )
    location = InventoryLocation.objects.create(name="Regal A", type=InventoryLocation.TYPE_SHELF, capacity=Decimal("200.00"))
    item = InventoryItem.objects.create(strain=strain, location=location, quantity=Decimal("10.00"))
    client.force_login(board_user)

    response = client.post(reverse("inventory:inventory_count_form"), data={f"item_{item.id}": "10.5"})

    item.refresh_from_db()
    assert response.status_code == 200
    assert "Inventurwerte muessen als ganze Zahl erfasst werden." in response.content.decode()
    assert item.quantity == Decimal("10.00")


@pytest.mark.django_db
def test_governance_tasks_form_hides_related_meeting_and_allows_delete(client, board_user):
    from apps.governance.models import BoardTask

    client.force_login(board_user)
    page = client.get(reverse("governance:tasks"))
    assert page.status_code == 200
    assert "Related Meeting" not in page.content.decode()
    assert "Zugehoerige Sitzung" not in page.content.decode()

    task = BoardTask.objects.create(
        title="Test Aufgabe",
        priority=BoardTask.PRIORITY_HIGH,
        status=BoardTask.STATUS_TODO,
        created_by=board_user,
    )
    response = client.post(reverse("governance:tasks"), data={"action": "delete", "task_id": task.id})

    assert response.status_code == 302
    assert BoardTask.objects.filter(id=task.id).exists() is False


@pytest.mark.django_db
def test_shift_create_and_detail_are_available_in_app(client, board_user):
    from apps.participation.models import Shift

    client.force_login(board_user)

    create_response = client.post(
        reverse("participation:shift_create"),
        data={
            "title": "Tresorcheck",
            "description": "Gemeinsamer Tresor- und Regalcheck",
            "starts_at": "2026-04-10T18:00",
            "ends_at": "2026-04-10T20:00",
            "required_members": "2",
        },
    )

    assert create_response.status_code == 302

    shift = Shift.objects.get(title="Tresorcheck")
    detail_response = client.get(reverse("participation:shift_detail", args=[shift.id]))
    calendar_response = client.get(reverse("participation:shift_calendar"))

    assert detail_response.status_code == 200
    assert "Tresorcheck" in detail_response.content.decode()
    assert calendar_response.status_code == 200
    assert reverse("participation:shift_detail", args=[shift.id]) in calendar_response.content.decode()
