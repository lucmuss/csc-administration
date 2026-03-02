from datetime import date
from decimal import Decimal

import pytest


@pytest.mark.django_db
def test_inventory_locations_count_and_discrepancies():
    from apps.inventory.models import InventoryItem, InventoryLocation, Strain
    from apps.inventory.services import InventoryCountService

    strain = Strain.objects.create(
        name="Critical",
        thc=Decimal("17.50"),
        cbd=Decimal("0.30"),
        price=Decimal("8.50"),
        stock=Decimal("100.00"),
    )
    location = InventoryLocation.objects.create(name="Vault 1", type=InventoryLocation.TYPE_VAULT, capacity=Decimal("500.00"))
    item = InventoryItem.objects.create(strain=strain, location=location, quantity=Decimal("50.00"))

    count = InventoryCountService.perform_count(
        count_date=date(2026, 3, 2),
        counted_quantities={item.id: Decimal("47.50")},
    )

    item.refresh_from_db()
    assert item.quantity == Decimal("47.50")
    assert item.last_counted == date(2026, 3, 2)
    assert count.items_counted == 1
    assert len(count.discrepancies) == 1
    assert count.discrepancies[0]["delta"] == "-2.50"


@pytest.mark.django_db
def test_inventory_move_and_quality_control():
    from apps.inventory.models import InventoryItem, InventoryLocation, Strain
    from apps.inventory.services import InventoryService, QualityControlService

    strain = Strain.objects.create(
        name="OG Kush",
        thc=Decimal("22.00"),
        cbd=Decimal("0.10"),
        price=Decimal("12.00"),
        stock=Decimal("80.00"),
    )
    source = InventoryLocation.objects.create(name="Dry Room", type=InventoryLocation.TYPE_DRY_ROOM, capacity=Decimal("300.00"))
    target = InventoryLocation.objects.create(name="Shelf A", type=InventoryLocation.TYPE_SHELF, capacity=Decimal("100.00"))
    source_item = InventoryItem.objects.create(strain=strain, location=source, quantity=Decimal("30.00"))

    InventoryService.move_stock(
        strain=strain,
        source=source,
        target=target,
        quantity=Decimal("10.00"),
    )
    QualityControlService.set_quality_grade(strain=strain, grade=Strain.QUALITY_A_PLUS)

    source_item.refresh_from_db()
    target_item = InventoryItem.objects.get(strain=strain, location=target)
    strain.refresh_from_db()

    assert source_item.quantity == Decimal("20.00")
    assert target_item.quantity == Decimal("10.00")
    assert strain.quality_grade == Strain.QUALITY_A_PLUS
