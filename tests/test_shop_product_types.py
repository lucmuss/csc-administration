import pytest
from django.core.management import call_command
from django.urls import reverse


@pytest.mark.django_db
def test_shop_filter_shows_cuttings_with_piece_unit(client, member_user):
    client.force_login(member_user)
    call_command("seed_demo_data")

    response = client.get(f"{reverse('orders:shop')}?type=cutting")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Stecklinge" in html
    assert "Steckling: Orange Bud" in html
    assert "1 Stk." in html
    assert "pro Stueck" in html
    assert "shop-card-compact__badge" in html
    assert "--shop-card-bg:" in html
    assert 'aria-label="Blue Dream zum Warenkorb hinzufuegen"' not in html
