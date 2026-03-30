from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Strain(models.Model):
    PRODUCT_TYPE_FLOWER = "flower"
    PRODUCT_TYPE_CUTTING = "cutting"
    PRODUCT_TYPE_EDIBLE = "edible"
    PRODUCT_TYPE_CHOICES = [
        (PRODUCT_TYPE_FLOWER, "Bluete"),
        (PRODUCT_TYPE_CUTTING, "Steckling"),
        (PRODUCT_TYPE_EDIBLE, "Edible"),
    ]

    QUALITY_A_PLUS = "A+"
    QUALITY_A = "A"
    QUALITY_B = "B"
    QUALITY_C = "C"
    QUALITY_CHOICES = [
        (QUALITY_A_PLUS, "A+"),
        (QUALITY_A, "A"),
        (QUALITY_B, "B"),
        (QUALITY_C, "C"),
    ]

    name = models.CharField(max_length=120, unique=True)
    thc = models.DecimalField(max_digits=5, decimal_places=2)
    cbd = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.DecimalField(max_digits=10, decimal_places=2)
    product_type = models.CharField(max_length=16, choices=PRODUCT_TYPE_CHOICES, default=PRODUCT_TYPE_FLOWER)
    quality_grade = models.CharField(max_length=2, choices=QUALITY_CHOICES, default=QUALITY_B)
    image = models.FileField(upload_to="strains/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def reserve(self, grams: Decimal) -> None:
        if grams <= 0:
            raise ValidationError("Menge muss > 0 sein")
        if grams > self.stock:
            raise ValidationError("Nicht genug Bestand")
        self.stock -= grams
        self.save(update_fields=["stock"])

    def release(self, grams: Decimal) -> None:
        if grams <= 0:
            raise ValidationError("Menge muss > 0 sein")
        self.stock += grams
        self.save(update_fields=["stock"])

    @property
    def is_weight_based(self) -> bool:
        return self.product_type == self.PRODUCT_TYPE_FLOWER

    @property
    def unit_label(self) -> str:
        return "g" if self.is_weight_based else "Stk."

    @property
    def unit_price_label(self) -> str:
        return "pro Gramm" if self.is_weight_based else "pro Stueck"

    @property
    def stock_display(self) -> str:
        return f"{self.stock} {self.unit_label}"


class InventoryLocation(models.Model):
    TYPE_DRY_ROOM = "dry_room"
    TYPE_VAULT = "vault"
    TYPE_SHELF = "shelf"
    TYPE_CHOICES = [
        (TYPE_DRY_ROOM, "Trockenraum"),
        (TYPE_VAULT, "Tresor"),
        (TYPE_SHELF, "Regal"),
    ]

    name = models.CharField(max_length=120, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_SHELF)
    capacity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    strain = models.ForeignKey(Strain, on_delete=models.PROTECT, related_name="inventory_items")
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name="items")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    last_counted = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["location__name", "strain__name"]
        unique_together = ("strain", "location")

    def __str__(self):
        return f"{self.strain.name} @ {self.location.name}"


class InventoryCount(models.Model):
    date = models.DateField()
    items_counted = models.PositiveIntegerField(default=0)
    discrepancies = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"Inventur {self.date}"


class Batch(models.Model):
    strain = models.ForeignKey(Strain, on_delete=models.PROTECT, related_name="batches")
    code = models.CharField(max_length=64, unique=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    harvested_at = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self):
        return self.code
