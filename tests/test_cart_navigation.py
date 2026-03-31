import pytest
from django.core import mail
from django.test import override_settings
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


@pytest.mark.django_db
def test_checkout_requires_confirmation_screen(client, member_user):
    from apps.inventory.models import Strain

    strain = Strain.objects.create(
        name="Channel",
        thc="18.00",
        cbd="0.30",
        price="8.00",
        stock="50.00",
    )
    client.force_login(member_user)
    session = client.session
    session["cart"] = {str(strain.id): "2"}
    session.save()

    response = client.post(reverse("orders:checkout"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "Bitte pruefe deine Reservierung noch einmal." in html
    assert "Jetzt verbindlich reservieren" in html


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_checkout_sends_reserved_order_email(client, member_user):
    from apps.inventory.models import Strain

    strain = Strain.objects.create(
        name="Blue Dream",
        thc="20.00",
        cbd="0.20",
        price="8.00",
        stock="50.00",
    )
    client.force_login(member_user)
    session = client.session
    session["cart"] = {str(strain.id): "2"}
    session.save()

    response = client.post(reverse("orders:checkout"), {"confirm": "yes"})

    assert response.status_code == 302
    assert response.url == reverse("orders:list")
    assert len(mail.outbox) == 1
    assert "reserviert" in mail.outbox[0].subject.lower()
    assert member_user.email in mail.outbox[0].to
