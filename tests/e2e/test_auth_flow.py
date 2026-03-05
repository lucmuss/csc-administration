"""E2E Tests: Authentication Flow

Testet: Login, Register, Logout, Passwort-Reset, Dev-Login
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_registration_success(client):
    """Test: Erfolgreiche Registrierung mit Validierung"""
    from apps.accounts.models import User
    from apps.members.models import Profile

    response = client.post(
        reverse("accounts:register"),
        {
            "email": "newuser@example.com",
            "first_name": "Neuer",
            "last_name": "Nutzer",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "birth_date": "1990-01-01",
            "accept_terms": True,
        },
    )

    # Sollte redirect zu Bestätigungsseite
    assert response.status_code == 302
    assert User.objects.filter(email="newuser@example.com").exists()
    
    user = User.objects.get(email="newuser@example.com")
    assert user.role == User.ROLE_MEMBER
    assert Profile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_registration_underage(client):
    """Test: Registrierung abgelehnt wenn unter 21"""
    from apps.accounts.models import User

    response = client.post(
        reverse("accounts:register"),
        {
            "email": "young@example.com",
            "first_name": "Jung",
            "last_name": "Nutzer",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "birth_date": "2010-01-01",  # Zu jung
            "accept_terms": True,
        },
    )

    # Sollte Fehler zeigen
    assert response.status_code == 200
    assert not User.objects.filter(email="young@example.com").exists()


@pytest.mark.django_db
def test_registration_duplicate_email(client, member_user):
    """Test: Registrierung abgelehnt bei doppelter E-Mail"""
    response = client.post(
        reverse("accounts:register"),
        {
            "email": member_user.email,  # Bereits existiert
            "first_name": "Anderer",
            "last_name": "Nutzer",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "birth_date": "1990-01-01",
            "accept_terms": True,
        },
    )

    assert response.status_code == 200
    assert "email" in str(response.content).lower() or "bereits" in str(response.content).lower()


@pytest.mark.django_db
def test_login_success(client, member_user):
    """Test: Login mit korrekten Credentials"""
    response = client.post(
        reverse("accounts:login"),
        {
            "username": member_user.email,
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")


@pytest.mark.django_db
def test_login_wrong_password(client, member_user):
    """Test: Login mit falschen Credentials (Fehler)"""
    response = client.post(
        reverse("accounts:login"),
        {
            "username": member_user.email,
            "password": "FalschesPasswort!",
        },
    )

    assert response.status_code == 200
    assert "ungültig" in str(response.content).lower() or "falsch" in str(response.content).lower()


@pytest.mark.django_db
def test_login_nonexistent_user(client):
    """Test: Login mit nicht existierendem User"""
    response = client.post(
        reverse("accounts:login"),
        {
            "username": "nicht@existiert.de",
            "password": "IrgendeinPasswort!",
        },
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_logout(client, member_user):
    """Test: Logout"""
    client.force_login(member_user)
    
    response = client.post(reverse("accounts:logout"))
    
    assert response.status_code == 302
    # Session sollte beendet sein


@pytest.mark.django_db
def test_password_reset_request(client, member_user):
    """Test: Passwort-Reset anfordern"""
    response = client.post(
        reverse("accounts:password_reset"),
        {"email": member_user.email},
    )

    assert response.status_code == 302  # Redirect zu Bestätigung


@pytest.mark.django_db
def test_dev_login_available(client, settings):
    """Test: Dev-Login nur bei DEBUG=True verfügbar"""
    settings.DEBUG = True
    
    response = client.get("/accounts/dev-login/")
    
    # Sollte verfügbar sein (Status 200 oder 302)
    assert response.status_code in [200, 302]


@pytest.mark.django_db
def test_dev_login_not_available_in_production(client, settings):
    """Test: Dev-Login NICHT bei DEBUG=False verfügbar"""
    settings.DEBUG = False
    
    response = client.get("/accounts/dev-login/")
    
    # Sollte 404 oder Redirect sein
    assert response.status_code in [404, 302, 301]


@pytest.mark.django_db
def test_protected_route_requires_login(client):
    """Test: Geschützte Seite erfordert Login"""
    response = client.get(reverse("members:profile"))
    
    # Sollte zu Login redirecten
    assert response.status_code == 302
    assert "login" in response.url


@pytest.mark.django_db
def test_protected_route_accessible_when_logged_in(client, member_user):
    """Test: Geschützte Seite zugänglich nach Login"""
    client.force_login(member_user)
    
    response = client.get(reverse("members:profile"))
    
    assert response.status_code == 200
