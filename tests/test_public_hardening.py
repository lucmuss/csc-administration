import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import date


@pytest.mark.django_db
@override_settings(HEALTH_ALLOWED_IPS=[])
def test_health_endpoint_is_forbidden_for_public_requests(client):
    response = client.get(reverse("core:health"), REMOTE_ADDR="203.0.113.25")

    assert response.status_code == 403


@pytest.fixture
def board_user(db):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="health-board@example.com",
        password="StrongPass123!",
        first_name="Hanna",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1988, 4, 5),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=200001,
        desired_join_date=date(2026, 4, 1),
        street_address="Rosa-Luxemburg-Strasse 12",
        postal_code="04103",
        city="Leipzig",
        phone="+4915111122233",
        bank_name="GLS",
        account_holder_name="Hanna Board",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        registration_completed_at=timezone.now(),
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE12500105170648489890",
        bic="GENODEM1GLS",
        account_holder="Hanna Board",
        mandate_reference="CSC-FIXTURE-HEALTH-BOARD",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


@pytest.mark.django_db
@override_settings(HEALTH_ALLOWED_IPS=[])
def test_health_endpoint_is_available_for_board_members(client, board_user):
    client.force_login(board_user)

    response = client.get(reverse("core:health"), REMOTE_ADDR="203.0.113.25")

    assert response.status_code == 200
