from decimal import Decimal

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_seed_demo_data_is_idempotent():
    from apps.core.models import SocialClub
    from apps.finance.models import Invoice
    from apps.inventory.models import Strain
    from apps.messaging.models import EmailGroup
    from apps.orders.models import Order

    call_command("seed_demo_data")
    call_command("seed_demo_data")

    assert Strain.objects.count() == 16
    assert Strain.objects.get(name="Orange Bud").price == Decimal("8.00")
    assert Strain.objects.get(name="Orange Bud").stock == Decimal("48.00")
    assert Strain.objects.get(name="Orange Bud").product_type == Strain.PRODUCT_TYPE_FLOWER
    assert Strain.objects.get(name="Orange Bud").card_tone == Strain.CARD_TONE_APRICOT
    assert Strain.objects.get(name="Steckling: Orange Bud").price == Decimal("5.00")
    assert Strain.objects.get(name="Steckling: Orange Bud").stock == Decimal("12.00")
    assert Strain.objects.get(name="Steckling: Orange Bud").product_type == Strain.PRODUCT_TYPE_CUTTING
    assert Strain.objects.get(name="Steckling: Orange Bud").card_tone == Strain.CARD_TONE_MINT
    assert Order.objects.count() == 5
    assert Invoice.objects.count() == 5
    assert SocialClub.objects.filter(name="Cannabis Social Club Muenchen Isar e.V.").exists()
    assert SocialClub.objects.filter(name="Cannabis Social Club Stuttgart Foehre").exists()
    assert EmailGroup.objects.filter(name="Regional Bayern").exists()
