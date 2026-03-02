from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.compliance.services import (
    detect_suspicious_activity_for_profile,
    ensure_prevention_info_for_first_dispense,
)
from apps.finance.services import create_invoice_for_order
from apps.inventory.models import Batch, Strain
from apps.members.models import Profile

from .models import Order, OrderItem


@dataclass
class CartLine:
    strain_id: int
    grams: Decimal


@transaction.atomic
def create_reserved_order(*, user, cart_lines: list[CartLine]) -> Order:
    if not cart_lines:
        raise ValidationError("Warenkorb ist leer")

    profile = Profile.objects.select_for_update().get(user=user)
    profile.reset_limits_if_due()
    if not profile.is_verified or profile.status != Profile.STATUS_ACTIVE:
        raise ValidationError("Mitglied ist nicht verifiziert")
    if profile.is_locked_for_orders:
        raise ValidationError("Mitglied ist fuer Bestellungen gesperrt")

    total_grams = Decimal("0.00")
    total_price = Decimal("0.00")
    strains = {}

    for line in cart_lines:
        if line.grams <= 0:
            raise ValidationError("Menge muss > 0 sein")
        strain = Strain.objects.select_for_update().get(id=line.strain_id, is_active=True)
        if strain.stock < line.grams:
            raise ValidationError(f"Nicht genug Bestand fuer {strain.name}")
        line_total = strain.price * line.grams
        total_grams += line.grams
        total_price += line_total
        strains[line.strain_id] = strain

    allowed, reason = profile.can_consume(total_grams)
    if not allowed:
        raise ValidationError(reason)

    if profile.balance < total_price:
        raise ValidationError("Nicht genug Guthaben")

    order = Order.objects.create(
        member=user,
        status=Order.STATUS_RESERVED,
        total=total_price,
        total_grams=total_grams,
        reserved_until=Order.reservation_deadline(),
        paid_with_balance=total_price,
    )

    for line in cart_lines:
        strain = strains[line.strain_id]
        line_total = strain.price * line.grams
        batch = (
            Batch.objects.select_for_update()
            .filter(
                strain=strain,
                is_active=True,
                quantity__gte=line.grams,
            )
            .order_by("harvested_at", "created_at")
            .first()
        )
        OrderItem.objects.create(
            order=order,
            strain=strain,
            batch=batch,
            quantity_grams=line.grams,
            unit_price=strain.price,
            total_price=line_total,
        )
        if batch:
            batch.quantity = F("quantity") - line.grams
            batch.save(update_fields=["quantity"])
        strain.stock = F("stock") - line.grams
        strain.save(update_fields=["stock"])

    profile.balance -= total_price
    profile.consume(total_grams)
    profile.last_activity = timezone.now()
    profile.save(update_fields=["balance", "daily_used", "monthly_used", "last_activity", "updated_at"])
    detect_suspicious_activity_for_profile(profile=profile)
    ensure_prevention_info_for_first_dispense(user=user, order=order)
    create_invoice_for_order(order=order)

    return order


@transaction.atomic
def release_expired_reservations(now=None) -> int:
    now = now or timezone.now()
    expired_orders = Order.objects.select_for_update().filter(
        status=Order.STATUS_RESERVED,
        reserved_until__lt=now,
    )
    count = 0
    for order in expired_orders:
        profile = Profile.objects.select_for_update().get(user=order.member)
        profile.balance += order.paid_with_balance
        profile.daily_used -= order.total_grams
        profile.monthly_used -= order.total_grams
        profile.save(update_fields=["balance", "daily_used", "monthly_used", "updated_at"])

        for item in order.items.select_related("strain", "batch"):
            strain = item.strain
            strain.stock += item.quantity_grams
            strain.save(update_fields=["stock"])
            if item.batch:
                batch = item.batch
                batch.quantity += item.quantity_grams
                batch.save(update_fields=["quantity"])

        order.status = Order.STATUS_CANCELLED
        order.save(update_fields=["status", "updated_at"])
        count += 1

    return count
