from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from apps.core.models import SocialClub
from apps.members.models import Profile, VerificationSubmission


@pytest.fixture
def superuser(db):
    User = get_user_model()
    return User.objects.create_superuser(
        email="superuser@example.com",
        password="StrongPass123!",
        first_name="Super",
        last_name="User",
    )


@pytest.mark.django_db
def test_admin_member_profile_changelist_is_accessible(client, superuser):
    client.force_login(superuser)
    response = client.get(reverse("admin:members_profile_changelist"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_verification_submission_changelist_is_accessible(client, superuser):
    client.force_login(superuser)
    response = client.get(reverse("admin:members_verificationsubmission_changelist"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_profile_search_by_email_returns_member(client, superuser, member_user):
    client.force_login(superuser)
    response = client.get(reverse("admin:members_profile_changelist"), {"q": member_user.email})
    assert response.status_code == 200
    assert member_user.email in response.content.decode("utf-8")


@pytest.mark.django_db
def test_registration_login_onboarding_profile_flow(client):
    club = SocialClub.objects.create(
        name="CSC Flow Club",
        email="flow-club@example.com",
        street_address="Flowstrasse 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49123456",
        federal_state=SocialClub.BUNDESLAND_SN,
        is_active=True,
        is_approved=True,
    )
    User = get_user_model()
    User.objects.create_user(
        email="board-flow@example.com",
        password="StrongPass123!",
        first_name="Board",
        last_name="Flow",
        role=User.ROLE_BOARD,
        is_staff=True,
        social_club=club,
    )
    registration_response = client.post(
        reverse("members:register"),
        data={
            "first_name": "Erika",
            "last_name": "Flow",
            "email": "erika-flow@example.com",
            "birth_date": "1990-01-01",
            "password": "StrongPass123!",
            "accept_terms": "on",
            "federal_state": SocialClub.BUNDESLAND_SN,
            "social_club": club.id,
        },
    )
    assert registration_response.status_code == 302
    if registration_response.url == reverse("accounts:login"):
        login_response = client.post(
            reverse("accounts:login"),
            data={
                "username": "erika-flow@example.com",
                "password": "StrongPass123!",
                "federal_state": SocialClub.BUNDESLAND_SN,
                "social_club": club.id,
            },
        )
        assert login_response.status_code == 302
        assert login_response.url == reverse("members:onboarding")
    else:
        assert registration_response.url == reverse("core:dashboard")

    onboarding_response = client.post(
        reverse("members:onboarding"),
        data={
            "desired_join_date": timezone.localdate().isoformat(),
            "street_address": "Flowstrasse 9",
            "postal_code": "04107",
            "city": "Leipzig",
            "phone": "+4915112345678",
            "iban": "DE44500105175407324931",
            "bic": "INGDDEFFXXX",
            "bank_name": "ING",
            "account_holder_name": "Erika Flow",
            "privacy_accepted": "on",
            "direct_debit_accepted": "on",
            "no_other_csc_membership": "on",
            "german_residence_confirmed": "on",
            "minimum_age_confirmed": "on",
            "id_document_confirmed": "on",
            "important_newsletter_opt_in": "on",
            "optional_newsletter_opt_in": "True",
            "application_notes": "Alles ausgefuellt",
        },
    )
    assert onboarding_response.status_code == 302
    assert onboarding_response.url == reverse("core:dashboard")

    profile_response = client.get(reverse("members:profile"))
    assert profile_response.status_code == 200
    assert "Nicht verifiziert" in profile_response.content.decode("utf-8")


@pytest.mark.django_db
def test_verification_submission_then_admin_approval_updates_profile_status(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    club = SocialClub.objects.create(
        name="CSC Verify Flow",
        email="verify-club@example.com",
        street_address="Verifystrasse 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49123457",
        is_active=True,
        is_approved=True,
    )
    User = get_user_model()
    board_user = User.objects.create_user(
        email="board-verify-flow@example.com",
        password="StrongPass123!",
        first_name="Board",
        last_name="Verify",
        role=User.ROLE_BOARD,
        is_staff=True,
        social_club=club,
    )
    Profile.objects.create(
        user=board_user,
        birth_date=date(1980, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=102001,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    member_user = User.objects.create_user(
        email="member-verify-flow@example.com",
        password="StrongPass123!",
        first_name="Mila",
        last_name="Flow",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    member_profile = Profile.objects.create(
        user=member_user,
        birth_date=date(1992, 1, 1),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        desired_join_date=timezone.localdate(),
        street_address="Mitgliedsweg 8",
        postal_code="04107",
        city="Leipzig",
        phone="+4915111111111",
        bank_name="ING",
        account_holder_name="Mila Flow",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        registration_completed_at=timezone.now(),
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    member_profile.sepa_mandates.create(
        iban="DE89370400440532013000",
        bic="COBADEFFXXX",
        account_holder="Mila Flow",
        mandate_reference="MANDATE-VERIFY-FLOW",
        is_active=True,
    )

    client.force_login(member_user)
    submission_response = client.post(
        reverse("members:verification"),
        data={
            "id_front_image": SimpleUploadedFile("front.jpg", b"front", content_type="image/jpeg"),
            "id_back_image": SimpleUploadedFile("back.jpg", b"back", content_type="image/jpeg"),
        },
    )
    assert submission_response.status_code == 302

    VerificationSubmission.objects.get(profile=member_profile, status=VerificationSubmission.STATUS_SUBMITTED)

    client.force_login(board_user)
    approval_response = client.post(
        reverse("members:verification_detail", args=[member_profile.id]),
        data={"action": "approve", "admin_notes": "Dokumente ok"},
        follow=True,
    )
    assert approval_response.status_code == 200

    member_profile.refresh_from_db()
    assert member_profile.is_verified is True
    assert member_profile.status == Profile.STATUS_ACTIVE
