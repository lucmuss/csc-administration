from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_cultivation_models_and_harvest_flow():
    from apps.accounts.models import User
    from apps.cultivation.models import GrowCycle, HarvestBatch, Plant, PlantLog
    from apps.inventory.models import Strain

    strain = Strain.objects.create(
        name="Lemon Haze",
        thc=Decimal("19.00"),
        cbd=Decimal("0.40"),
        price=Decimal("9.50"),
        stock=Decimal("0.00"),
    )
    actor = User.objects.create_user(
        email="cultivation@example.com",
        password="StrongPass123!",
        first_name="Cult",
        last_name="Admin",
        role=User.ROLE_STAFF,
        is_staff=True,
    )
    cycle = GrowCycle.objects.create(
        name="Cycle Lemon",
        start_date=date(2026, 1, 1),
        expected_harvest_date=date(2026, 3, 1),
        status=GrowCycle.STATUS_ACTIVE,
        created_by=actor,
    )
    plant = Plant.objects.create(
        grow_cycle=cycle,
        strain=strain,
        plant_number="101",
        planting_date=date(2026, 1, 20),
        status=Plant.STATUS_FLOWERING,
        created_by=actor,
    )

    PlantLog.objects.create(
        plant=plant,
        date=date(2026, 2, 1),
        log_type=PlantLog.LOG_TYPE_FERTILIZING,
        products_used="NPK 3-1-5",
        notes="Gute Entwicklung",
        created_by=actor,
    )

    harvest = HarvestBatch.objects.create(
        batch_number="BATCH-LH-001",
        harvest_date=date(2026, 3, 1),
        total_weight_fresh=Decimal("120.00"),
        total_weight_dried=Decimal("30.00"),
        created_by=actor,
    )
    harvest.plants.add(plant)
    plant.status = Plant.STATUS_HARVESTED
    plant.actual_yield_grams = Decimal("30.00")
    plant.save(update_fields=["status", "actual_yield_grams", "updated_at"])
    strain.stock = Decimal("30.00")
    strain.save(update_fields=["stock"])

    assert harvest.total_weight_dried == Decimal("30.00")
    assert plant.logs.count() == 1

    plant.refresh_from_db()
    strain.refresh_from_db()
    assert harvest.batch_number == "BATCH-LH-001"
    assert plant.status == Plant.STATUS_HARVESTED
    assert strain.stock == Decimal("30.00")


@pytest.mark.django_db
def test_cultivation_management_commands_output(capsys):
    call_command("check_harvest_readiness")
    call_command("generate_grow_report")
    output = capsys.readouterr().out

    assert "Anbau-Bericht" in output
