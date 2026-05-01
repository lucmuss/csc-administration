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


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_admin_completion_sends_notification_with_invoice_attachment(client, member_user, admin_user):
    from apps.inventory.models import Strain
    from apps.orders.models import Order

    strain = Strain.objects.create(
        name="Northern Lights",
        thc="19.00",
        cbd="0.30",
        price="9.00",
        stock="80.00",
    )

    client.force_login(member_user)
    session = client.session
    session["cart"] = {str(strain.id): "2"}
    session.save()
    reserve_response = client.post(reverse("orders:checkout"), {"confirm": "yes"})
    assert reserve_response.status_code == 302

    order = Order.objects.latest("id")

    client.force_login(admin_user)
    complete_response = client.post(
        reverse("orders:admin_action", args=[order.id]),
        {"action": "complete", "confirm": "yes"},
    )
    assert complete_response.status_code == 302

    subjects = [message.subject.lower() for message in mail.outbox]
    assert any("reserviert" in subject for subject in subjects)
    assert any("aktualisiert" in subject for subject in subjects)

    completed_mail = next(msg for msg in mail.outbox if "aktualisiert" in msg.subject.lower())
    attachment_names = {attachment[0] for attachment in completed_mail.attachments}
    assert any(name.endswith(".pdf") and name.startswith("INV-") for name in attachment_names)
