from datetime import date
from decimal import Decimal

import pytest


@pytest.mark.django_db
def test_seed_to_sale_trace(member_user):
    from apps.cultivation.models import GrowCycle, HarvestBatch, Plant
    from apps.inventory.models import Batch, Strain
    from apps.orders.models import OrderItem
    from apps.orders.services import CartLine, create_reserved_order

    strain = Strain.objects.create(
        name="Silver Haze",
        thc=Decimal("21.00"),
        cbd=Decimal("0.20"),
        price=Decimal("11.00"),
        stock=Decimal("50.00"),
    )
    cycle = GrowCycle.objects.create(
        name="Seed to Sale Cycle",
        start_date=date(2026, 1, 1),
        expected_harvest_date=date(2026, 3, 1),
        status=GrowCycle.STATUS_ACTIVE,
        created_by=member_user,
    )
    plant = Plant.objects.create(
        grow_cycle=cycle,
        strain=strain,
        plant_number="SH-001",
        planting_date=date(2026, 1, 10),
        status=Plant.STATUS_FLOWERING,
        expected_yield_grams=Decimal("80.00"),
        created_by=member_user,
    )
    harvest_batch = HarvestBatch.objects.create(
        batch_number="HB-SH-01",
        harvest_date=date(2026, 2, 25),
        total_weight_fresh=Decimal("200.00"),
        total_weight_dried=Decimal("50.00"),
        created_by=member_user,
    )
    harvest_batch.plants.add(plant)

    inventory_batch = Batch.objects.create(
        strain=strain,
        code="BATCH-SH-01",
        harvested_at=date(2026, 2, 25),
        quantity=Decimal("50.00"),
        is_active=True,
    )

    order = create_reserved_order(
        user=member_user,
        cart_lines=[CartLine(strain_id=strain.id, grams=Decimal("5.00"))],
    )
    order_item = OrderItem.objects.select_related("batch", "strain").get(order=order)
    inventory_batch.refresh_from_db()

    assert order_item.batch is not None
    assert order_item.batch.code == "BATCH-SH-01"
    assert inventory_batch.quantity == Decimal("45.00")
    assert harvest_batch.plants.filter(pk=plant.pk).exists()
