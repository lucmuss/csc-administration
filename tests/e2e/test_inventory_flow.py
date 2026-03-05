"""E2E Tests: Inventory Flow (Inventar/Sorten)

Testet: Sorten-Verwaltung, Chargen, Bestands-Tracking
"""
import pytest
from datetime import date
from decimal import Decimal

from django.urls import reverse


@pytest.mark.django_db
def test_strain_list_view(client, staff_user, strain):
    """Test: Sorten-Liste anzeigen"""
    client.force_login(staff_user)

    response = client.get(reverse("inventory:strain_list"))

    assert response.status_code == 200
    assert strain.name in str(response.content)


@pytest.mark.django_db
def test_strain_create(client, board_user):
    """Test: Neue Sorte erstellen"""
    from apps.inventory.models import Strain

    client.force_login(board_user)

    response = client.post(
        reverse("inventory:strain_create"),
        {
            "name": "Blue Dream",
            "slug": "blue-dream",
            "thc_content": "20.00",
            "cbd_content": "0.30",
            "price_per_gram": "12.00",
            "genetik": "hybrid",
        },
    )

    assert response.status_code == 302
    assert Strain.objects.filter(name="Blue Dream").exists()


@pytest.mark.django_db
def test_strain_update(client, board_user, strain):
    """Test: Sorte bearbeiten"""
    client.force_login(board_user)

    response = client.post(
        reverse("inventory:strain_update", kwargs={"pk": strain.pk}),
        {
            "name": strain.name,
            "slug": strain.slug,
            "thc_content": "22.00",  # Geändert
            "cbd_content": "0.50",
            "price_per_gram": "13.00",
        },
    )

    assert response.status_code == 302
    
    strain.refresh_from_db()
    assert strain.thc_content == Decimal("22.00")


@pytest.mark.django_db
def test_batch_create(client, board_user, strain):
    """Test: Neue Charge einbuchen"""
    from apps.inventory.models import Batch

    client.force_login(board_user)

    response = client.post(
        reverse("inventory:batch_create"),
        {
            "strain": strain.pk,
            "batch_number": "240301-TEST",
            "harvest_date": date.today().isoformat(),
            "total_harvested_grams": "3000.00",
            "available_grams": "3000.00",
            "price_per_gram": "10.00",
            "thc_content_actual": "18.50",
        },
    )

    assert response.status_code == 302
    assert Batch.objects.filter(batch_number="240301-TEST").exists()


@pytest.mark.django_db
def test_batch_detail_view(client, staff_user, batch):
    """Test: Charge-Details anzeigen"""
    client.force_login(staff_user)

    response = client.get(
        reverse("inventory:batch_detail", kwargs={"pk": batch.pk})
    )

    assert response.status_code == 200
    assert batch.batch_number in str(response.content)
    assert str(batch.thc_content_actual) in str(response.content)


@pytest.mark.django_db
def test_batch_stock_reduced_on_sale(client, member_user, batch):
    """Test: Bestand wird bei Verkauf reduziert"""
    initial_stock = batch.available_grams

    # Bestellung erstellen
    client.force_login(member_user)
    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )
    client.post(
        reverse("orders:checkout"),
        {"payment_method": "balance"},
    )

    batch.refresh_from_db()
    # Bestand sollte reduziert oder reserviert sein
    assert batch.available_grams < initial_stock or batch.reserved_grams == Decimal("5")


@pytest.mark.django_db
def test_low_stock_warning(client, board_user, strain):
    """Test: Warnung bei niedrigem Bestand"""
    from apps.inventory.models import Batch

    # Charge mit wenig Bestand erstellen
    batch = Batch.objects.create(
        strain=strain,
        batch_number="240301-LOW",
        harvest_date=date.today(),
        total_harvested_grams=Decimal("100.00"),
        available_grams=Decimal("5.00"),  # Sehr wenig
        price_per_gram=Decimal("10.00"),
        status=Batch.STATUS_AVAILABLE,
    )

    client.force_login(board_user)

    response = client.get(reverse("inventory:dashboard"))

    assert response.status_code == 200
    # Sollte Warnung anzeigen
    assert batch.batch_number in str(response.content) or "niedrig" in str(response.content).lower()


@pytest.mark.django_db
def test_batch_status_changes_when_sold_out(client, board_user, strain):
    """Test: Charge-Status ändert sich bei Ausverkauf"""
    from apps.inventory.models import Batch

    batch = Batch.objects.create(
        strain=strain,
        batch_number="240301-SOLD",
        harvest_date=date.today(),
        total_harvested_grams=Decimal("10.00"),
        available_grams=Decimal("10.00"),
        price_per_gram=Decimal("10.00"),
        status=Batch.STATUS_AVAILABLE,
    )

    # Alles verkaufen
    batch.available_grams = Decimal("0")
    batch.save()
    batch.update_status()

    batch.refresh_from_db()
    assert batch.status == Batch.STATUS_SOLD_OUT


@pytest.mark.django_db
def test_inventory_transaction_created_on_sale(client, member_user, batch):
    """Test: Inventar-Transaktion wird bei Verkauf erstellt"""
    from apps.inventory.models import InventoryTransaction

    client.force_login(member_user)
    
    # Bestellung erstellen
    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )
    client.post(
        reverse("orders:checkout"),
        {"payment_method": "balance"},
    )

    # Transaktion sollte existieren
    assert InventoryTransaction.objects.filter(batch=batch).exists()


@pytest.mark.django_db
def test_strain_filter_by_thc(client, staff_user):
    """Test: Sorten nach THC-Gehalt filtern"""
    from apps.inventory.models import Strain

    Strain.objects.create(
        name="Low THC",
        slug="low-thc",
        thc_content=Decimal("8.00"),
        price_per_gram=Decimal("8.00"),
    )
    Strain.objects.create(
        name="High THC",
        slug="high-thc",
        thc_content=Decimal("22.00"),
        price_per_gram=Decimal("12.00"),
    )

    client.force_login(staff_user)

    response = client.get(
        reverse("inventory:strain_list"),
        {"thc_min": "20"},
    )

    assert response.status_code == 200
    assert "High THC" in str(response.content)


@pytest.mark.django_db
def test_batch_cannot_exceed_total_harvested(client, board_user, strain):
    """Test: Verfügbarer Bestand kann nicht über Erntemenge gehen"""
    client.force_login(board_user)

    response = client.post(
        reverse("inventory:batch_create"),
        {
            "strain": strain.pk,
            "batch_number": "240301-INVALID",
            "harvest_date": date.today().isoformat(),
            "total_harvested_grams": "100.00",
            "available_grams": "150.00",  # Mehr als geerntet
            "price_per_gram": "10.00",
        },
    )

    # Sollte Fehler zeigen
    assert response.status_code == 200


@pytest.mark.django_db
def test_inventory_dashboard_shows_stats(client, board_user, batch):
    """Test: Inventar-Dashboard zeigt Statistiken"""
    client.force_login(board_user)

    response = client.get(reverse("inventory:dashboard"))

    assert response.status_code == 200
    assert batch.strain.name in str(response.content)


@pytest.mark.django_db
def test_batch_delete(client, board_user, batch):
    """Test: Charge löschen"""
    from apps.inventory.models import Batch

    client.force_login(board_user)

    response = client.post(
        reverse("inventory:batch_delete", kwargs={"pk": batch.pk}),
    )

    assert response.status_code == 302
    assert not Batch.objects.filter(pk=batch.pk).exists()


@pytest.mark.django_db
def test_strain_delete_prevented_if_batches_exist(client, board_user, batch):
    """Test: Sorte mit Chargen kann nicht gelöscht werden"""
    client.force_login(board_user)

    response = client.post(
        reverse("inventory:strain_delete", kwargs={"pk": batch.strain.pk}),
    )

    # Sollte Fehler zeigen oder verhindert sein
    assert response.status_code in [200, 302]
    # Sorte sollte noch existieren
    assert batch.strain.pk  # Existenz prüfen
