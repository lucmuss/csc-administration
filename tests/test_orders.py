from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError


@pytest.mark.django_db
def test_reserved_order_updates_balance_stock_and_limits(member_user):
    from apps.inventory.models import Strain
    from apps.members.models import Profile
    from apps.orders.models import Order
    from apps.orders.services import CartLine, create_reserved_order

    strain = Strain.objects.create(
        name="Orange Bud",
        thc=Decimal("18.00"),
        cbd=Decimal("0.50"),
        price=Decimal("10.00"),
        stock=Decimal("100.00"),
    )

    order = create_reserved_order(
        user=member_user,
        cart_lines=[CartLine(strain_id=strain.id, grams=Decimal("5.00"))],
    )

    assert order.status == Order.STATUS_RESERVED
    assert order.total == Decimal("50.00")

    strain.refresh_from_db()
    profile = Profile.objects.get(user=member_user)

    assert strain.stock == Decimal("95.00")
    assert profile.balance == Decimal("150.00")
    assert profile.daily_used == Decimal("5.00")
    assert profile.monthly_used == Decimal("5.00")


@pytest.mark.django_db
def test_order_rejects_when_daily_limit_exceeded(member_user):
    from apps.inventory.models import Strain
    from apps.members.models import Profile
    from apps.orders.services import CartLine, create_reserved_order

    profile = Profile.objects.get(user=member_user)
    profile.daily_used = Decimal("10.00")
    profile.monthly_used = Decimal("30.00")
    profile.save(update_fields=["daily_used", "monthly_used"])

    strain = Strain.objects.create(
        name="Blue Dream",
        thc=Decimal("20.00"),
        cbd=Decimal("0.30"),
        price=Decimal("9.00"),
        stock=Decimal("100.00"),
    )

    with pytest.raises(ValidationError):
        create_reserved_order(
            user=member_user,
            cart_lines=[CartLine(strain_id=strain.id, grams=Decimal("16.00"))],
        )
