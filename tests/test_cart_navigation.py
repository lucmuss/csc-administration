import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_member_navigation_contains_cart_link(client, member_user):
    client.force_login(member_user)
    session = client.session
    session["cart"] = {"1": "2"}
    session.save()

    response = client.get(reverse("orders:shop"))

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert reverse("orders:cart") in html
    assert "Warenkorb (1)" in html
