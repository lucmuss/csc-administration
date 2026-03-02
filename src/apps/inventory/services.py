from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import InventoryCount, InventoryItem, InventoryLocation, Strain


class InventoryService:
    @staticmethod
    @transaction.atomic
    def move_stock(*, strain: Strain, source: InventoryLocation, target: InventoryLocation, quantity: Decimal) -> None:
        if quantity <= 0:
            raise ValidationError("Menge muss > 0 sein")

        source_item = InventoryItem.objects.select_for_update().get(strain=strain, location=source)
        if source_item.quantity < quantity:
            raise ValidationError("Nicht genug Bestand am Quelllagerort")

        target_item, _ = InventoryItem.objects.select_for_update().get_or_create(
            strain=strain,
            location=target,
            defaults={"quantity": Decimal("0.00")},
        )

        source_item.quantity -= quantity
        target_item.quantity += quantity
        source_item.save(update_fields=["quantity"])
        target_item.save(update_fields=["quantity"])


class InventoryCountService:
    @staticmethod
    @transaction.atomic
    def perform_count(*, count_date: date, counted_quantities: dict[int, str | Decimal]) -> InventoryCount:
        discrepancies = []
        counted_items = 0

        for item_id, quantity in counted_quantities.items():
            item = InventoryItem.objects.select_for_update().get(id=item_id)
            counted = Decimal(str(quantity))
            delta = counted - item.quantity
            counted_items += 1

            if delta != Decimal("0.00"):
                discrepancies.append(
                    {
                        "item_id": item.id,
                        "strain": item.strain.name,
                        "location": item.location.name,
                        "expected": str(item.quantity),
                        "counted": str(counted),
                        "delta": str(delta),
                    }
                )

            item.quantity = counted
            item.last_counted = count_date
            item.save(update_fields=["quantity", "last_counted"])

        return InventoryCount.objects.create(
            date=count_date,
            items_counted=counted_items,
            discrepancies=discrepancies,
        )


class QualityControlService:
    @staticmethod
    def set_quality_grade(*, strain: Strain, grade: str) -> Strain:
        valid = {choice[0] for choice in Strain.QUALITY_CHOICES}
        if grade not in valid:
            raise ValidationError("Ungueltiger Quality Grade")
        strain.quality_grade = grade
        strain.save(update_fields=["quality_grade"])
        return strain
