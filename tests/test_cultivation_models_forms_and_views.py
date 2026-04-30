from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.cultivation.forms import GrowCycleForm
from apps.cultivation.models import GrowCycle, HarvestBatch, Plant
from apps.inventory.models import InventoryItem, InventoryLocation, Strain
from apps.members.models import Profile


@pytest.fixture
def cultivation_admin(db):
    user = get_user_model().objects.create_superuser(
        email="cult-admin@example.com",
        password="StrongPass123!",
        first_name="Cult",
        last_name="Admin",
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1980, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    return user


@pytest.mark.django_db
def test_grow_cycle_form_rejects_past_start_and_invalid_harvest_order():
    form = GrowCycleForm(
        data={
            "name": "GC",
            "description": "x",
            "start_date": (date.today() - timedelta(days=1)).isoformat(),
            "expected_harvest_date": (date.today() - timedelta(days=2)).isoformat(),
            "responsible_member": "",
            "location": "Raum 1",
            "notes": "",
        }
    )
    assert form.is_valid() is False


@pytest.mark.django_db
def test_plant_save_generates_qr_code_id():
    cycle = GrowCycle.objects.create(
        name="Cycle 1",
        start_date=date.today(),
        expected_harvest_date=date.today() + timedelta(days=60),
    )
    strain = Strain.objects.create(name="Cult Strain", thc=18, cbd=0.2, price=9, stock=100)
    plant = Plant.objects.create(
        grow_cycle=cycle,
        strain=strain,
        planting_date=date.today(),
        expected_yield_grams=Decimal("20.00"),
    )

    assert plant.qr_code_id.startswith("PLANT-")


@pytest.mark.django_db
def test_harvest_batch_autogenerates_batch_number():
    batch = HarvestBatch.objects.create(
        harvest_date=date.today(),
        total_weight_fresh=Decimal("100.00"),
    )
    assert batch.batch_number.startswith("H-")


@pytest.mark.django_db
def test_harvest_assign_to_inventory_creates_or_updates_inventory_item(client, cultivation_admin):
    cycle = GrowCycle.objects.create(
        name="Cycle Assign",
        start_date=date.today(),
        expected_harvest_date=date.today() + timedelta(days=45),
    )
    strain = Strain.objects.create(name="Assign Strain", thc=20, cbd=0.1, price=10, stock=100)
    plant = Plant.objects.create(grow_cycle=cycle, strain=strain, planting_date=date.today(), expected_yield_grams=10)
    batch = HarvestBatch.objects.create(
        harvest_date=date.today(),
        total_weight_fresh=Decimal("50.00"),
        total_weight_dried=Decimal("12.50"),
        curing_end_date=date.today(),
    )
    batch.plants.add(plant)
    location = InventoryLocation.objects.create(name="Vault X", type=InventoryLocation.TYPE_VAULT, capacity=500)

    client.force_login(cultivation_admin)
    response = client.post(
        reverse("cultivation:harvest_assign_inventory", args=[batch.pk]),
        data={"location": location.pk},
        follow=True,
    )

    assert response.status_code == 200
    batch.refresh_from_db()
    assert batch.assigned_to_inventory is True
    item = InventoryItem.objects.get(strain=strain, location=location)
    assert item.quantity == Decimal("12.50")


@pytest.mark.django_db
def test_plant_stats_api_returns_counts(client, cultivation_admin):
    cycle = GrowCycle.objects.create(
        name="Cycle API",
        start_date=date.today(),
        expected_harvest_date=date.today() + timedelta(days=30),
    )
    strain = Strain.objects.create(name="API Strain", thc=16, cbd=0.2, price=8, stock=80)
    Plant.objects.create(grow_cycle=cycle, strain=strain, planting_date=date.today(), status=Plant.STATUS_GROWING)

    client.force_login(cultivation_admin)
    response = client.get(reverse("cultivation:api_plant_stats"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
