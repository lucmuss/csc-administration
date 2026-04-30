import pytest
from django.urls import reverse

from apps.core.club import ACTIVE_FEDERAL_STATE_COOKIE, ACTIVE_FEDERAL_STATE_SESSION_KEY
from apps.core.models import SocialClub


@pytest.mark.django_db
def test_regional_social_club_page_filters_by_federal_state(client):
    SocialClub.objects.create(
        name="CSC Leipzig",
        email="leipzig@example.com",
        street_address="Strasse 1",
        postal_code="04109",
        city="Leipzig",
        federal_state="SN",
        phone="+49123",
        is_active=True,
        is_approved=True,
    )
    SocialClub.objects.create(
        name="CSC Muenchen",
        email="muenchen@example.com",
        street_address="Strasse 2",
        postal_code="80331",
        city="Muenchen",
        federal_state="BY",
        phone="+49124",
        is_active=True,
        is_approved=True,
    )

    response = client.get(reverse("core:social_club_regional_list"), {"federal_state": "SN"})
    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "CSC Leipzig" in html
    assert "CSC Muenchen" not in html


@pytest.mark.django_db
def test_switch_federal_state_persists_in_session_and_cookie(client):
    response = client.post(
        reverse("core:social_club_state_switch"),
        data={"federal_state": "SN", "next": reverse("core:social_club_regional_list")},
    )
    assert response.status_code == 302
    assert client.session.get(ACTIVE_FEDERAL_STATE_SESSION_KEY) == "SN"
    assert response.cookies.get(ACTIVE_FEDERAL_STATE_COOKIE) is not None


@pytest.mark.django_db
def test_regional_social_club_page_supports_ajax_filter(client):
    SocialClub.objects.create(
        name="CSC Dresden",
        email="dresden@example.com",
        street_address="Strasse 3",
        postal_code="01067",
        city="Dresden",
        federal_state="SN",
        phone="+49125",
        is_active=True,
        is_approved=True,
    )
    response = client.get(
        reverse("core:social_club_regional_list"),
        {"federal_state": "SN"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    payload = response.json()
    assert "CSC Dresden" in payload["html"]
