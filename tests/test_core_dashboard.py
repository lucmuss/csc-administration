from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone


@pytest.fixture
def board_user(db):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="board-dashboard@example.com",
        password="StrongPass123!",
        first_name="Bea",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100001,
        desired_join_date=date(2026, 4, 1),
        street_address="Karl-Liebknecht-Strasse 9",
        postal_code="04107",
        city="Leipzig",
        phone="+4915112345678",
        bank_name="ING",
        account_holder_name="Bea Board",
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
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Bea Board",
        mandate_reference="CSC-FIXTURE-BOARD",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


@pytest.mark.django_db
def test_board_dashboard_does_not_link_feature_audit(client, board_user):
    client.force_login(board_user)

    response = client.get(reverse("core:dashboard"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Feature-Audit" not in content
    assert "/board/features/" not in content
    assert "Mitglieder-Cockpit" in content
    assert "Mitgliederversammlung anlegen" in content


@pytest.mark.django_db
def test_feature_audit_route_is_removed(client, board_user):
    client.force_login(board_user)

    response = client.get("/board/features/")

    assert response.status_code == 404
