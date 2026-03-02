from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_cultivation_models_and_harvest_flow():
    from apps.cultivation.models import BatchConnection, GrowthLog, MotherPlant, Plant
    from apps.cultivation.services import GrowLogService, HarvestService
    from apps.inventory.models import Batch, Strain

    strain = Strain.objects.create(
        name="Lemon Haze",
        thc=Decimal("19.00"),
        cbd=Decimal("0.40"),
        price=Decimal("9.50"),
        stock=Decimal("0.00"),
    )
    mother = MotherPlant.objects.create(
        strain=strain,
        planted_date=date(2025, 12, 1),
        genetics="Sativa dominant",
    )
    cutting = mother.cuttings.create(planted_date=date(2026, 1, 10), status="rooted", rooting_date=date(2026, 1, 18))
    plant = Plant.objects.create(
        cutting=cutting,
        room="Flower Room 1",
        planting_date=date(2026, 1, 20),
        growth_stage=Plant.STAGE_FLOWERING,
    )

    GrowLogService.add_entry(
        plant=plant,
        entry_date=date(2026, 2, 1),
        activity_type=GrowthLog.ACTIVITY_NUTRIENTS,
        nutrients="NPK 3-1-5",
        notes="Gute Entwicklung",
    )

    harvest = HarvestService.document_harvest(
        plant=plant,
        harvest_date=date(2026, 3, 1),
        wet_weight=Decimal("120.00"),
        dry_weight=Decimal("30.00"),
        batch_code="BATCH-LH-001",
    )

    assert harvest.dry_weight == Decimal("30.00")
    assert plant.growth_logs.count() == 1

    plant.refresh_from_db()
    strain.refresh_from_db()
    batch = Batch.objects.get(code="BATCH-LH-001")
    connection = BatchConnection.objects.get(harvest=harvest)

    assert plant.growth_stage == Plant.STAGE_HARVESTED
    assert strain.stock == Decimal("30.00")
    assert batch.quantity == Decimal("30.00")
    assert connection.batch_id == batch.id


@pytest.mark.django_db
def test_cultivation_management_commands_output(capsys):
    call_command("check_harvest_readiness")
    call_command("generate_grow_report")
    output = capsys.readouterr().out

    assert "Anbau-Bericht" in output
