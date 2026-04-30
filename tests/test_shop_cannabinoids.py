from decimal import Decimal

import pytest
from django.urls import reverse

from apps.inventory.models import Strain


@pytest.mark.django_db
def test_shop_displays_extended_cannabinoids_when_provided(client, member_user):
    Strain.objects.create(
        name="Canna Profile X",
        thc=Decimal("22.10"),
        cbd=Decimal("1.20"),
        cbg=Decimal("0.60"),
        cbn=Decimal("0.20"),
        cbc=Decimal("0.30"),
        cbv=Decimal("0.10"),
        price=Decimal("9.90"),
        stock=Decimal("50.00"),
        is_active=True,
        social_club=member_user.social_club,
    )
    client.force_login(member_user)
    response = client.get(reverse("orders:shop"))
    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "CBG 0.60%" in html
    assert "CBN 0.20%" in html
    assert "CBC 0.30%" in html
    assert "CBV 0.10%" in html
