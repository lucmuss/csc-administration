from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.inventory.models import Strain
from apps.orders.models import Order
from apps.orders.services import CartLine, cancel_reserved_order, complete_reserved_order, create_reserved_order, release_expired_reservations


@pytest.mark.django_db
def test_create_reserved_order_rejects_empty_cart(member_user):
    with pytest.raises(ValidationError):
        create_reserved_order(user=member_user, cart_lines=[])


@pytest.mark.django_db
def test_create_reserved_order_rejects_non_integer_quantity_for_non_weight_product(member_user):
    item = Strain.objects.create(
        name="Merch Tee",
        product_type=Strain.PRODUCT_TYPE_MERCH,
        thc=Decimal("0.00"),
        cbd=Decimal("0.00"),
        price=Decimal("20.00"),
        stock=Decimal("10.00"),
    )
    with pytest.raises(ValidationError):
        create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=item.id, quantity=Decimal("1.5"))])


@pytest.mark.django_db
def test_release_expired_reservations_restores_stock(member_user):
    strain = Strain.objects.create(name="Expired Test", thc=18, cbd=0.2, price=5, stock=20)
    order = create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=strain.id, quantity=Decimal("2"))])
    Order.objects.filter(id=order.id).update(reserved_until=timezone.now() - timezone.timedelta(hours=1))

    released = release_expired_reservations(now=timezone.now())
    strain.refresh_from_db()
    order.refresh_from_db()

    assert released >= 1
    assert order.status == Order.STATUS_CANCELLED
    assert strain.stock == Decimal("20")


@pytest.mark.django_db
def test_cancel_reserved_order_marks_invoice_cancelled(member_user):
    strain = Strain.objects.create(name="Cancel Test", thc=18, cbd=0.1, price=6, stock=20)
    order = create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=strain.id, quantity=Decimal("2"))])

    cancel_reserved_order(order=order)
    order.refresh_from_db()
    order.invoice.refresh_from_db()

    assert order.status == Order.STATUS_CANCELLED
    assert order.invoice.status == order.invoice.STATUS_CANCELLED


@pytest.mark.django_db
def test_complete_reserved_order_rejects_non_reserved(member_user):
    strain = Strain.objects.create(name="Complete Test", thc=18, cbd=0.1, price=4, stock=20)
    order = create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=strain.id, quantity=Decimal("2"))])
    order.status = Order.STATUS_CANCELLED
    order.save(update_fields=["status", "updated_at"])

    with pytest.raises(ValidationError):
        complete_reserved_order(order=order)
