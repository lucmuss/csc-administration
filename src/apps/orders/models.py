from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.inventory.models import Batch, Strain


class _OrderCompatManager(models.Manager):
    @staticmethod
    def _normalize(kwargs: dict):
        data = dict(kwargs)
        member_value = data.get("member")
        if hasattr(member_value, "user"):
            data["member"] = member_value.user
        return data

    def create(self, **kwargs):
        return super().create(**self._normalize(kwargs))

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self._normalize(kwargs))

    def get(self, *args, **kwargs):
        return super().get(*args, **self._normalize(kwargs))


class Order(models.Model):
    STATUS_RESERVED = "reserved"
    STATUS_COMPLETED = "completed"
    STATUS_CONFIRMED = STATUS_COMPLETED
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_RESERVED, "Reserviert"),
        (STATUS_COMPLETED, "Abgeschlossen"),
        (STATUS_CANCELLED, "Storniert"),
        (STATUS_EXPIRED, "Abgelaufen"),
    ]

    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RESERVED)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_grams = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    reserved_until = models.DateTimeField()
    paid_with_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = _OrderCompatManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} - {self.member.email}"

    @staticmethod
    def reservation_deadline() -> timezone.datetime:
        return timezone.now() + timedelta(hours=48)

    @property
    def total_grams_display(self) -> str:
        return f"{self.total_grams} g"

    @property
    def self_cancel_deadline(self):
        return self.created_at + timedelta(hours=getattr(settings, "ORDER_SELF_CANCEL_HOURS", 24))

    @property
    def can_self_cancel(self) -> bool:
        return self.status == self.STATUS_RESERVED and timezone.now() <= self.self_cancel_deadline


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    strain = models.ForeignKey(Strain, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, blank=True, null=True, related_name="order_items")
    quantity_grams = models.DecimalField(max_digits=8, decimal_places=2)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.strain.name} {self.quantity_display}"

    @property
    def quantity_display(self) -> str:
        return f"{self.quantity_grams} {self.strain.unit_label}"
