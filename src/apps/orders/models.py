from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.inventory.models import Strain


class Order(models.Model):
    STATUS_RESERVED = "reserved"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_RESERVED, "Reserviert"),
        (STATUS_COMPLETED, "Abgeschlossen"),
        (STATUS_CANCELLED, "Storniert"),
    ]

    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RESERVED)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_grams = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    reserved_until = models.DateTimeField()
    paid_with_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} - {self.member.email}"

    @staticmethod
    def reservation_deadline() -> timezone.datetime:
        return timezone.now() + timedelta(hours=48)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    strain = models.ForeignKey(Strain, on_delete=models.PROTECT)
    quantity_grams = models.DecimalField(max_digits=8, decimal_places=2)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.strain.name} {self.quantity_grams}g"
