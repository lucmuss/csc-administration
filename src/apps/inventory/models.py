from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Strain(models.Model):
    name = models.CharField(max_length=120, unique=True)
    thc = models.DecimalField(max_digits=5, decimal_places=2)
    cbd = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.DecimalField(max_digits=10, decimal_places=2)
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
