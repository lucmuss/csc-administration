from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.models import SocialClub
from apps.cultivation.models import GrowCycle, Plant
from apps.inventory.models import Strain
from apps.members.models import Profile


@pytest.fixture
def cultivation_admin(db):
    User = get_user_model()
    club = SocialClub.objects.create(
        name="CSC Cultivation E2E",
        email="cultivation-e2e@example.com",
        street_address="Anbauweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49111111111",
        is_active=True,
        is_approved=True,
    )
    user = User.objects.create_superuser(
        email="cultivation-admin@example.com",
        password="StrongPass123!",
        first_name="Cultivation",
        last_name="Admin",
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1985, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=303001,
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    return user


@pytest.fixture
def cultivation_strain(cultivation_admin):
    return Strain.objects.create(
        social_club=cultivation_admin.social_club,
        name="Cultivation Orange",
        thc=Decimal("19.00"),
        cbd=Decimal("0.30"),
        price=Decimal("8.90"),
        stock=Decimal("100.00"),
        product_type=Strain.PRODUCT_TYPE_FLOWER,
    )


@pytest.mark.django_db
def test_cultivation_dashboard_loads(client, cultivation_admin):
    client.force_login(cultivation_admin)
    response = client.get(reverse("cultivation:dashboard"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_grow_cycle_create_and_detail(client, cultivation_admin):
    client.force_login(cultivation_admin)
    response = client.post(
        reverse("cultivation:grow_cycle_create"),
        data={
            "name": "Grow Q2",
            "description": "Fruehjahrslauf",
            "start_date": date.today().isoformat(),
            "expected_harvest_date": (date.today() + timedelta(days=90)).isoformat(),
            "status": GrowCycle.STATUS_ACTIVE,
            "location": "Raum A",
        },
    )
    assert response.status_code == 302
    cycle = GrowCycle.objects.get(name="Grow Q2")
    detail = client.get(reverse("cultivation:grow_cycle_detail", args=[cycle.id]))
    assert detail.status_code == 200
    assert "Grow Q2" in detail.content.decode("utf-8")


@pytest.mark.django_db
def test_plant_create_and_log_entry(client, cultivation_admin, cultivation_strain):
    cycle = GrowCycle.objects.create(
        name="Grow Plant",
        description="Mit Pflanze",
        start_date=date.today(),
        expected_harvest_date=date.today() + timedelta(days=80),
        status=GrowCycle.STATUS_ACTIVE,
        created_by=cultivation_admin,
    )
    client.force_login(cultivation_admin)
    create_response = client.post(
        reverse("cultivation:plant_create"),
        data={
            "grow_cycle": str(cycle.id),
            "strain": cultivation_strain.id,
            "plant_number": "101",
            "planting_date": date.today().isoformat(),
            "status": Plant.STATUS_GROWING,
            "expected_yield_grams": "120.00",
            "actual_yield_grams": "0.00",
        },
    )
    assert create_response.status_code == 302
    plant = Plant.objects.get(plant_number="101")

    log_response = client.post(
        reverse("cultivation:plant_log_create", args=[plant.id]),
        data={
            "log_type": "observation",
            "date": "2026-04-10T11:30",
            "notes": "Gesunder Zustand",
            "products_used": "",
        },
    )
    assert log_response.status_code == 302
    detail_response = client.get(reverse("cultivation:plant_detail", args=[plant.id]))
    assert detail_response.status_code == 200
    assert "Gesunder Zustand" in detail_response.content.decode("utf-8")
