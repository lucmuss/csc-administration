from datetime import date
from decimal import Decimal

import pytest


@pytest.mark.django_db
def test_seed_to_sale_trace(member_user):
    from apps.cultivation.models import MotherPlant, Plant
    from apps.cultivation.services import HarvestService, SeedToSaleService
    from apps.inventory.models import Strain
    from apps.orders.services import CartLine, create_reserved_order

    strain = Strain.objects.create(
        name="Silver Haze",
        thc=Decimal("21.00"),
        cbd=Decimal("0.20"),
        price=Decimal("11.00"),
        stock=Decimal("0.00"),
    )
    mother = MotherPlant.objects.create(
        strain=strain,
        planted_date=date(2025, 11, 1),
        genetics="Haze line",
    )
    cutting = mother.cuttings.create(planted_date=date(2026, 1, 1), status="rooted", rooting_date=date(2026, 1, 8))
    plant = Plant.objects.create(
        cutting=cutting,
        room="Room A",
        planting_date=date(2026, 1, 10),
        growth_stage=Plant.STAGE_FLOWERING,
    )

    HarvestService.document_harvest(
        plant=plant,
        harvest_date=date(2026, 2, 25),
        wet_weight=Decimal("200.00"),
        dry_weight=Decimal("50.00"),
        batch_code="BATCH-SH-01",
    )

    order = create_reserved_order(
        user=member_user,
        cart_lines=[CartLine(strain_id=strain.id, grams=Decimal("5.00"))],
    )

    trace = SeedToSaleService.trace_order(order_id=order.id)

    assert len(trace) == 1
    assert trace[0]["batch"] is not None
    assert trace[0]["batch"].code == "BATCH-SH-01"
    assert trace[0]["harvest"] is not None
    assert trace[0]["plant"] is not None
    assert trace[0]["mother_plant"] is not None
    assert trace[0]["mother_plant"].id == mother.id
