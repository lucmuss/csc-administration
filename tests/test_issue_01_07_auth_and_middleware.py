import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from apps.accounts.views import _client_ip, _login_limit_key
from apps.members.models import Profile


@pytest.mark.django_db
def test_login_sets_social_club_and_state_cookie(client, member_user):
    from apps.core.models import SocialClub

    club = SocialClub.objects.create(
        name="CSC Login Club",
        email="login-club@example.com",
        street_address="Testweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+4912345",
        federal_state=SocialClub.BUNDESLAND_SN,
        is_active=True,
        is_approved=True,
    )
    member_user.social_club = club
    member_user.save(update_fields=["social_club"])

    response = client.post(
        reverse("accounts:login"),
        data={
            "username": member_user.email,
            "password": "StrongPass123!",
            "social_club": club.id,
            "federal_state": SocialClub.BUNDESLAND_SN,
        },
    )

    assert response.status_code == 302
    assert response.cookies["active_social_club_id"].value == str(club.id)
    assert response.cookies["active_federal_state"].value == SocialClub.BUNDESLAND_SN


@pytest.mark.django_db
def test_member_cannot_login_into_other_social_club(client, member_user):
    from apps.core.models import SocialClub

    own_club = SocialClub.objects.create(
        name="CSC Own Club",
        email="own-club@example.com",
        street_address="Ownweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49123",
        is_active=True,
        is_approved=True,
    )
    other_club = SocialClub.objects.create(
        name="CSC Other Club",
        email="other-club@example.com",
        street_address="Otherweg 2",
        postal_code="04109",
        city="Leipzig",
        phone="+49456",
        is_active=True,
        is_approved=True,
    )
    member_user.social_club = own_club
    member_user.save(update_fields=["social_club"])

    response = client.post(
        reverse("accounts:login"),
        data={"username": member_user.email, "password": "StrongPass123!", "social_club": other_club.id},
    )

    assert response.status_code == 200
    assert "gehoert nicht zum ausgewaehlten Social Club" in response.content.decode("utf-8")


def test_client_ip_prefers_forwarded_header(rf):
    request = rf.get("/", HTTP_X_FORWARDED_FOR="198.51.100.10, 10.0.0.2", REMOTE_ADDR="10.0.0.3")
    assert _client_ip(request) == "198.51.100.10"


def test_login_limit_key_normalizes_username():
    assert _login_limit_key("127.0.0.1", " USER@Example.com ") == "login-rate-limit:127.0.0.1:user@example.com"


@pytest.mark.django_db
def test_middleware_redirects_incomplete_member_to_onboarding(client, member_user):
    member_user.profile.registration_completed_at = None
    member_user.profile.save(update_fields=["registration_completed_at", "updated_at"])
    client.force_login(member_user)

    response = client.get(reverse("core:dashboard"))

    assert response.status_code == 302
    assert response.url == reverse("members:onboarding")


@pytest.mark.django_db
def test_middleware_allows_pending_member_finance_routes(client, member_user):
    member_user.profile.is_verified = False
    member_user.profile.status = Profile.STATUS_PENDING
    member_user.profile.save(update_fields=["is_verified", "status", "updated_at"])
    client.force_login(member_user)

    response = client.get(reverse("finance:invoice_list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_middleware_blocks_pending_member_orders_and_adds_message(client, member_user):
    member_user.profile.is_verified = False
    member_user.profile.status = Profile.STATUS_PENDING
    member_user.profile.registration_completed_at = timezone.now()
    member_user.profile.save(update_fields=["is_verified", "status", "registration_completed_at", "updated_at"])
    client.force_login(member_user)

    response = client.get(reverse("orders:shop"), follow=True)

    assert response.status_code == 200
    _ = [str(message) for message in get_messages(response.wsgi_request)]
    assert response.request["PATH_INFO"] == reverse("core:dashboard")
