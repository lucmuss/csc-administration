from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from apps.compliance.services import (
    detect_suspicious_activity_for_profile,
    ensure_prevention_info_for_first_dispense,
)
from apps.finance.services import apply_monthly_membership_credits, available_balance, create_invoice_for_order, settle_order_with_balance
from apps.inventory.models import Batch, Strain
from apps.members.models import Profile

from .models import Order, OrderItem


@dataclass
class CartLine:
    strain_id: int
    quantity: Decimal


@transaction.atomic
def create_reserved_order(*, user, cart_lines: list[CartLine]) -> Order:
    if not cart_lines:
        raise ValidationError("Warenkorb ist leer")

    release_expired_reservations(now=timezone.now())
    apply_monthly_membership_credits()
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
        if line.quantity <= 0:
            raise ValidationError("Menge muss > 0 sein")
        strain = Strain.objects.select_for_update().get(id=line.strain_id, is_active=True)
        if not strain.is_weight_based and line.quantity != line.quantity.to_integral_value():
            raise ValidationError(f"{strain.name} kann nur in ganzen Stueckzahlen bestellt werden")
        if strain.stock < line.quantity:
            raise ValidationError(f"Nicht genug Bestand fuer {strain.name}")
        line_total = strain.price * line.quantity
        if strain.is_weight_based:
            total_grams += line.quantity
        total_price += line_total
        strains[line.strain_id] = strain

    allowed, reason = profile.can_consume(total_grams)
    if not allowed:
        raise ValidationError(reason)

    free_balance = available_balance(profile)
    if free_balance < total_price:
        reserved_total = profile.user.orders.filter(status=Order.STATUS_RESERVED).aggregate(total=Sum("total"))["total"] or Decimal("0.00")
        raise ValidationError(
            (
                f"Nicht genug verfuegbares Guthaben. Gesamtguthaben: {profile.balance} EUR, "
                f"bereits reserviert: {reserved_total} EUR, aktuell verfuegbar: {free_balance} EUR."
            )
        )

    order = Order.objects.create(
        member=user,
        status=Order.STATUS_RESERVED,
        total=total_price,
        total_grams=total_grams,
        reserved_until=Order.reservation_deadline(),
        paid_with_balance=Decimal("0.00"),
    )

    for line in cart_lines:
        strain = strains[line.strain_id]
        line_total = strain.price * line.quantity
        batch = (
            Batch.objects.select_for_update()
            .filter(
                strain=strain,
                is_active=True,
                quantity__gte=line.quantity,
            )
            .order_by("harvested_at", "created_at")
            .first()
            if strain.is_weight_based
            else None
        )
        OrderItem.objects.create(
            order=order,
            strain=strain,
            batch=batch,
            quantity_grams=line.quantity,
            unit_price=strain.price,
            total_price=line_total,
        )
        if batch:
            batch.quantity = F("quantity") - line.quantity
            batch.save(update_fields=["quantity"])
        strain.stock = F("stock") - line.quantity
        strain.save(update_fields=["stock"])

    profile.last_activity = timezone.now()
    profile.save(update_fields=["last_activity", "updated_at"])
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


@transaction.atomic
def cancel_reserved_order(*, order: Order) -> Order:
    if order.status != Order.STATUS_RESERVED:
        raise ValidationError("Nur reservierte Bestellungen koennen storniert werden")

    profile = Profile.objects.select_for_update().get(user=order.member)

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

    if hasattr(order, "invoice") and order.invoice:
        invoice = order.invoice
        invoice.status = invoice.STATUS_CANCELLED
        invoice.save(update_fields=["status", "updated_at"])

    return order


@transaction.atomic
def member_cancel_reserved_order(*, order: Order) -> Order:
    if not order.can_self_cancel:
        raise ValidationError("Diese Reservierung kann nicht mehr selbst storniert werden.")
    cancelled_order = cancel_reserved_order(order=order)
    if hasattr(cancelled_order, "invoice") and cancelled_order.invoice:
        cancelled_order.invoice.delete()
    cancelled_order.delete()
    return cancelled_order


@transaction.atomic
def complete_reserved_order(*, order: Order) -> Order:
    if order.status != Order.STATUS_RESERVED:
        raise ValidationError("Nur reservierte Bestellungen koennen freigegeben werden")

    profile = Profile.objects.select_for_update().get(user=order.member)
    profile.reset_limits_if_due()
    allowed, reason = profile.can_consume(order.total_grams)
    if not allowed:
        raise ValidationError(reason)
    try:
        settle_order_with_balance(order=order)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if order.total_grams > Decimal("0.00"):
        profile.consume(order.total_grams)
    order.status = Order.STATUS_COMPLETED
    order.save(update_fields=["status", "updated_at"])
    return order
