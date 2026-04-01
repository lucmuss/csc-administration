from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.members.forms import MemberOnboardingForm


@pytest.fixture
def board_user(db):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="board-defaults@example.com",
        password="StrongPass123!",
        first_name="Berta",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1985, 5, 5),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=101001,
        desired_join_date=date(2026, 4, 1),
        street_address="Teststrasse 1",
        postal_code="04107",
        city="Leipzig",
        phone="+4915112345678",
        bank_name="GLS",
        account_holder_name="Berta Board",
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
        account_holder="Berta Board",
        mandate_reference="CSC-FIXTURE-BOARD-DEFAULTS",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


@pytest.mark.django_db
def test_onboarding_form_defaults_join_date_to_first_day_of_next_month(member_user):
    member_user.profile.desired_join_date = None
    member_user.profile.save(update_fields=["desired_join_date", "updated_at"])

    form = MemberOnboardingForm(profile=member_user.profile)
    today = timezone.localdate()
    expected = date(today.year + 1, 1, 1) if today.month == 12 else date(today.year, today.month + 1, 1)

    assert form.fields["desired_join_date"].initial == expected


@pytest.mark.django_db
def test_pending_member_after_onboarding_has_limited_access(client, member_user):
    from apps.members.models import Profile

    member_user.profile.status = Profile.STATUS_PENDING
    member_user.profile.save(update_fields=["status", "updated_at"])
    client.force_login(member_user)

    shop_response = client.get(reverse("orders:shop"))
    directory_response = client.get(reverse("members:directory"))
    finance_response = client.get(reverse("finance:dashboard"))

    assert shop_response.status_code == 302
    assert shop_response.url == reverse("core:dashboard")
    assert directory_response.status_code == 302
    assert directory_response.url == reverse("core:dashboard")
    assert finance_response.status_code == 200


@pytest.mark.django_db
def test_governance_task_form_prefills_due_date_and_owner(client, board_user):
    client.force_login(board_user)

    response = client.get(reverse("governance:tasks"))

    assert response.status_code == 200
    form = response.context["form"]
    assert form["due_date"].value() == timezone.localdate() + timedelta(days=5)
    assert str(form["owner"].value()) == str(board_user.id)


@pytest.mark.django_db
def test_governance_meeting_form_prefills_chairperson_and_online_meeting(client, board_user):
    client.force_login(board_user)

    response = client.get(reverse("governance:meetings"))

    assert response.status_code == 200
    form = response.context["form"]
    assert form["location"].value() == "Online-Meeting"
    assert str(form["chairperson"].value()) == str(board_user.id)


@pytest.mark.django_db
def test_inventory_location_can_be_deleted(client, board_user):
    from apps.inventory.models import InventoryLocation

    location = InventoryLocation.objects.create(name="Regal X", type=InventoryLocation.TYPE_SHELF, capacity=Decimal("42.00"))
    client.force_login(board_user)

    response = client.post(reverse("inventory:location_delete", args=[location.id]))

    assert response.status_code == 302
    assert InventoryLocation.objects.filter(id=location.id).exists() is False


@pytest.mark.django_db
def test_member_import_preview_page_renders_with_session_payload(client, board_user):
    client.force_login(board_user)
    session = client.session
    session["member_import_payload"] = {
        "filename": "mitglieder.csv",
        "headers": ["E-Mail-Adresse", "Vorname"],
        "preview_rows": [{"E-Mail-Adresse": "test@example.com", "Vorname": "Test"}],
        "raw_text": "E-Mail-Adresse,Vorname\ntest@example.com,Test\n",
        "delimiter": ",",
    }
    session.save()

    response = client.get(reverse("members:import"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "mitglieder.csv" in html
    assert "test@example.com" in html
