from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.inventory.models import Batch, Strain


class MotherPlant(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_RETIRED = "retired"
    STATUS_DISEASED = "diseased"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Aktiv"),
        (STATUS_RETIRED, "Stillgelegt"),
        (STATUS_DISEASED, "Krank"),
    ]

    strain = models.ForeignKey(Strain, on_delete=models.PROTECT, related_name="mother_plants")
    planted_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    genetics = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-planted_date", "id"]

    def __str__(self):
        return f"{self.strain.name} (Mutter #{self.id})"


class Cutting(models.Model):
    STATUS_PLANTED = "planted"
    STATUS_ROOTED = "rooted"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PLANTED, "Gesteckt"),
        (STATUS_ROOTED, "Bewurzelt"),
        (STATUS_FAILED, "Fehlgeschlagen"),
    ]

    mother_plant = models.ForeignKey(MotherPlant, on_delete=models.CASCADE, related_name="cuttings")
    planted_date = models.DateField()
    rooting_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANTED)

    class Meta:
        ordering = ["-planted_date", "id"]

    def __str__(self):
        return f"Steckling #{self.id} ({self.mother_plant.strain.name})"


class Plant(models.Model):
    STAGE_SEEDLING = "seedling"
    STAGE_VEGETATIVE = "vegetative"
    STAGE_FLOWERING = "flowering"
    STAGE_HARVESTED = "harvested"
    STAGE_CHOICES = [
        (STAGE_SEEDLING, "Jungpflanze"),
        (STAGE_VEGETATIVE, "Wachstum"),
        (STAGE_FLOWERING, "Bluete"),
        (STAGE_HARVESTED, "Geerntet"),
    ]

    cutting = models.OneToOneField(Cutting, on_delete=models.PROTECT, related_name="plant")
    room = models.CharField(max_length=120)
    planting_date = models.DateField()
    growth_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default=STAGE_SEEDLING)

    class Meta:
        ordering = ["-planting_date", "id"]

    def __str__(self):
        return f"Pflanze #{self.id} ({self.cutting.mother_plant.strain.name})"


class GrowthLog(models.Model):
    ACTIVITY_WATERING = "watering"
    ACTIVITY_NUTRIENTS = "nutrients"
    ACTIVITY_PRUNING = "pruning"
    ACTIVITY_HEALTH = "health"
    ACTIVITY_CHOICES = [
        (ACTIVITY_WATERING, "Bewaesserung"),
        (ACTIVITY_NUTRIENTS, "Duengung"),
        (ACTIVITY_PRUNING, "Schnitt"),
        (ACTIVITY_HEALTH, "Gesundheitscheck"),
    ]

    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name="growth_logs")
    date = models.DateField()
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    notes = models.TextField(blank=True)
    nutrients = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date", "-id"]


class Harvest(models.Model):
    plant = models.OneToOneField(Plant, on_delete=models.PROTECT, related_name="harvest")
    harvest_date = models.DateField()
    wet_weight = models.DecimalField(max_digits=8, decimal_places=2)
    dry_weight = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["-harvest_date", "-id"]

    def clean(self):
        if self.wet_weight < Decimal("0.00") or self.dry_weight < Decimal("0.00"):
            raise ValidationError("Gewicht darf nicht negativ sein")
        if self.dry_weight > self.wet_weight:
            raise ValidationError("Trockengewicht kann nicht groesser als Nassgewicht sein")


class BatchConnection(models.Model):
    harvest = models.OneToOneField(Harvest, on_delete=models.CASCADE, related_name="batch_connection")
    batch = models.OneToOneField(Batch, on_delete=models.PROTECT, related_name="harvest_connection")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Ernte #{self.harvest.id} -> Charge {self.batch.code}"
