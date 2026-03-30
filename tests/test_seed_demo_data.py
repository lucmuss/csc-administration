from decimal import Decimal

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_seed_demo_data_is_idempotent():
    from apps.finance.models import Invoice
    from apps.inventory.models import Strain
    from apps.orders.models import Order

    call_command("seed_demo_data")
    call_command("seed_demo_data")

    assert Strain.objects.count() == 16
    assert Strain.objects.get(name="Orange Bud").price == Decimal("8.00")
    assert Strain.objects.get(name="Orange Bud").stock == Decimal("48.00")
    assert Strain.objects.get(name="Steckling: Orange Bud").price == Decimal("5.00")
    assert Strain.objects.get(name="Steckling: Orange Bud").stock == Decimal("12.00")
    assert Order.objects.count() == 3
    assert Invoice.objects.count() == 3
