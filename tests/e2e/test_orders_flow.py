"""E2E Tests: Orders Flow (Bestellungen/Shop)

Testet: Warenkorb, Bestellung, Limit-Prüfung, Stornierung
"""
import pytest
from datetime import date
from decimal import Decimal

from django.urls import reverse


@pytest.mark.django_db
def test_add_to_cart(client, member_user, batch):
    """Test: Produkt in Warenkorb legen"""
    client.force_login(member_user)

    response = client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )

    assert response.status_code == 302
    
    # Session sollte Warenkorb enthalten
    session = client.session
    assert "cart" in session


@pytest.mark.django_db
def test_view_cart(client, member_user, batch):
    """Test: Warenkorb anzeigen"""
    client.force_login(member_user)

    # Produkt hinzufügen
    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )

    response = client.get(reverse("orders:cart"))
    
    assert response.status_code == 200
    assert batch.strain.name in str(response.content)


@pytest.mark.django_db
def test_remove_from_cart(client, member_user, batch):
    """Test: Produkt aus Warenkorb entfernen"""
    client.force_login(member_user)

    # Produkt hinzufügen
    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )

    # Produkt entfernen
    response = client.post(
        reverse("orders:remove_from_cart"),
        {"batch_id": batch.pk},
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_checkout_creates_order(client, member_user, batch):
    """Test: Bestellung aufgeben"""
    from apps.orders.models import Order

    client.force_login(member_user)

    # Produkt hinzufügen
    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )

    # Checkout
    response = client.post(
        reverse("orders:checkout"),
        {
            "payment_method": "balance",
        },
    )

    assert response.status_code == 302
    assert Order.objects.filter(member=member_user.profile).exists()


@pytest.mark.django_db
def test_daily_limit_enforced(client, member_user, batch):
    """Test: Limit-Prüfung (25g/Tag) - Hard Block"""
    client.force_login(member_user)

    # Versuche mehr als 25g zu bestellen
    response = client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 30,  # Über dem Limit
        },
    )

    # Sollte Fehler zeigen oder nicht hinzufügen
    assert response.status_code in [200, 302]
    
    # Bei 302 sollte eine Fehlermeldung in der Session sein
    if response.status_code == 302:
        assert "limit" in str(response.url).lower() or any(
            "limit" in str(m).lower() 
            for m in client.session.get("messages", [])
        )


@pytest.mark.django_db
def test_monthly_limit_enforced(client, member_user, batch):
    """Test: Limit-Prüfung (50g/Monat) - Hard Block"""
    from apps.orders.models import Order, OrderItem

    client.force_login(member_user)

    # Setze monatlichen Verbrauch auf fast 50g
    member_user.profile.daily_used = Decimal("0")
    member_user.profile.monthly_used = Decimal("45")
    member_user.profile.save()

    # Versuche weitere 10g zu bestellen (würde über 50g gehen)
    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 10,
        },
    )

    response = client.post(
        reverse("orders:checkout"),
        {
            "payment_method": "balance",
        },
    )

    # Sollte blockiert werden
    assert response.status_code == 200 or "limit" in str(response.content).lower()


@pytest.mark.django_db
def test_insufficient_balance_blocks_order(client, member_user, batch):
    """Test: Unzureichendes Guthaben blockiert Bestellung"""
    client.force_login(member_user)

    # Guthaben auf 0 setzen
    member_user.profile.balance = Decimal("0")
    member_user.profile.save()

    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )

    response = client.post(
        reverse("orders:checkout"),
        {
            "payment_method": "balance",
        },
    )

    # Sollte Fehler zeigen
    assert response.status_code == 200


@pytest.mark.django_db
def test_cancel_order(client, member_user, batch):
    """Test: Bestellung stornieren"""
    from apps.orders.models import Order

    client.force_login(member_user)

    # Bestellung erstellen
    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )

    client.post(
        reverse("orders:checkout"),
        {
            "payment_method": "balance",
        },
    )

    order = Order.objects.get(member=member_user.profile)

    # Stornieren
    response = client.post(
        reverse("orders:cancel", kwargs={"pk": order.pk}),
    )

    assert response.status_code == 302
    
    order.refresh_from_db()
    assert order.status == Order.STATUS_CANCELLED


@pytest.mark.django_db
def test_admin_confirm_order(client, staff_user, member_user, batch):
    """Test: Admin bestätigt Bestellung"""
    from apps.orders.models import Order

    # Bestellung erstellen (als Mitglied)
    client.force_login(member_user)
    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )
    client.post(
        reverse("orders:checkout"),
        {
            "payment_method": "balance",
        },
    )
    order = Order.objects.get(member=member_user.profile)
    client.logout()

    # Als Staff bestätigen
    client.force_login(staff_user)
    response = client.post(
        reverse("orders:admin_confirm", kwargs={"pk": order.pk}),
    )

    assert response.status_code == 302
    
    order.refresh_from_db()
    assert order.status == Order.STATUS_CONFIRMED


@pytest.mark.django_db
def test_order_history_view(client, member_user, batch):
    """Test: Bestellhistorie anzeigen"""
    client.force_login(member_user)

    # Bestellung erstellen
    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )
    client.post(
        reverse("orders:checkout"),
        {
            "payment_method": "balance",
        },
    )

    response = client.get(reverse("orders:history"))

    assert response.status_code == 200
    assert batch.strain.name in str(response.content)


@pytest.mark.django_db
def test_reservation_timeout(client, member_user, batch):
    """Test: Reservierung läuft nach 48h ab"""
    from apps.orders.models import Order
    from django.utils import timezone
    from datetime import timedelta

    client.force_login(member_user)

    # Bestellung erstellen
    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )
    client.post(
        reverse("orders:checkout"),
        {
            "payment_method": "balance",
        },
    )

    order = Order.objects.get(member=member_user.profile)
    
    # Zeit zurücksetzen (mehr als 48h)
    order.created_at = timezone.now() - timedelta(hours=49)
    order.save()

    # Expire Command ausführen
    from apps.orders.management.commands.expire_reservations import Command
    Command().handle()

    order.refresh_from_db()
    assert order.status == Order.STATUS_EXPIRED


@pytest.mark.django_db
def test_batch_stock_reduced_after_order(client, member_user, batch):
    """Test: Bestand wird nach Bestellung reduziert"""
    from apps.orders.models import Order

    initial_stock = batch.available_grams

    client.force_login(member_user)

    client.post(
        reverse("orders:add_to_cart"),
        {
            "batch_id": batch.pk,
            "quantity": 5,
        },
    )
    client.post(
        reverse("orders:checkout"),
        {
            "payment_method": "balance",
        },
    )

    batch.refresh_from_db()
    # Bestand sollte reduziert sein (oder reserviert)
    assert batch.available_grams < initial_stock or batch.reserved_grams > 0
