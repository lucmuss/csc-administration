from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.inventory.models import Batch, Strain
from apps.orders.models import OrderItem

from .models import BatchConnection, GrowthLog, Harvest, MotherPlant, Plant


class GrowLogService:
    @staticmethod
    def add_entry(*, plant: Plant, entry_date: date, activity_type: str, notes: str = "", nutrients: str = "") -> GrowthLog:
        return GrowthLog.objects.create(
            plant=plant,
            date=entry_date,
            activity_type=activity_type,
            notes=notes,
            nutrients=nutrients,
        )


class HarvestService:
    @staticmethod
    def estimate_harvest_date(*, plant: Plant) -> date:
        if plant.growth_stage == Plant.STAGE_FLOWERING:
            return plant.planting_date + timedelta(days=70)
        if plant.growth_stage == Plant.STAGE_VEGETATIVE:
            return plant.planting_date + timedelta(days=98)
        return plant.planting_date + timedelta(days=112)

    @staticmethod
    @transaction.atomic
    def document_harvest(
        *,
        plant: Plant,
        harvest_date: date,
        wet_weight: Decimal,
        dry_weight: Decimal,
        batch_code: str | None = None,
    ) -> Harvest:
        if Harvest.objects.filter(plant=plant).exists():
            raise ValidationError("Fuer diese Pflanze existiert bereits eine Ernte")

        harvest = Harvest.objects.create(
            plant=plant,
            harvest_date=harvest_date,
            wet_weight=wet_weight,
            dry_weight=dry_weight,
        )

        strain: Strain = plant.cutting.mother_plant.strain
        batch = Batch.objects.create(
            strain=strain,
            code=batch_code or f"BATCH-{timezone.now():%Y%m%d}-{plant.id}",
            quantity=dry_weight,
            harvested_at=harvest_date,
            is_active=True,
        )
        BatchConnection.objects.create(harvest=harvest, batch=batch)

        strain.stock += dry_weight
        strain.save(update_fields=["stock"])

        plant.growth_stage = Plant.STAGE_HARVESTED
        plant.save(update_fields=["growth_stage"])

        return harvest


class SeedToSaleService:
    @staticmethod
    def trace_order_item(*, order_item: OrderItem) -> dict:
        if not order_item.batch:
            return {
                "order_item_id": order_item.id,
                "batch": None,
                "harvest": None,
                "plant": None,
                "cutting": None,
                "mother_plant": None,
            }

        connection = BatchConnection.objects.select_related(
            "harvest__plant__cutting__mother_plant"
        ).filter(batch=order_item.batch).first()

        harvest = connection.harvest if connection else None
        plant = harvest.plant if harvest else None
        cutting = plant.cutting if plant else None
        mother = cutting.mother_plant if cutting else None

        return {
            "order_item_id": order_item.id,
            "batch": order_item.batch,
            "harvest": harvest,
            "plant": plant,
            "cutting": cutting,
            "mother_plant": mother,
        }

    @staticmethod
    def trace_order(*, order_id: int) -> list[dict]:
        order_items = OrderItem.objects.select_related("batch").filter(order_id=order_id)
        return [SeedToSaleService.trace_order_item(order_item=item) for item in order_items]


class CultivationDashboardService:
    @staticmethod
    def get_overview() -> dict:
        upcoming_harvests = []
        for plant in Plant.objects.select_related("cutting__mother_plant__strain").exclude(growth_stage=Plant.STAGE_HARVESTED):
            upcoming_harvests.append(
                {
                    "plant": plant,
                    "estimated_harvest": HarvestService.estimate_harvest_date(plant=plant),
                }
            )

        return {
            "mother_count": MotherPlant.objects.count(),
            "active_plants": Plant.objects.exclude(growth_stage=Plant.STAGE_HARVESTED).count(),
            "harvest_count": Harvest.objects.count(),
            "upcoming_harvests": sorted(upcoming_harvests, key=lambda x: x["estimated_harvest"])[:10],
        }
