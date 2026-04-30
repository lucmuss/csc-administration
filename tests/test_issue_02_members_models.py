from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.members.models import Profile, VerificationSubmission


@pytest.mark.django_db
def test_profile_clean_rejects_underage_member(member_user, settings):
    settings.MEMBER_MINIMUM_AGE = 21
    member_user.profile.birth_date = timezone.localdate().replace(year=timezone.localdate().year - 20)

    with pytest.raises(ValidationError):
        member_user.profile.clean()


@pytest.mark.django_db
def test_profile_allocate_member_number_assigns_next_value():
    from apps.accounts.models import User

    first_user = User.objects.create_user(
        email="member-number-1@example.com",
        password="StrongPass123!",
        first_name="A",
        last_name="One",
        role=User.ROLE_MEMBER,
    )
    first_profile = Profile.objects.create(
        user=first_user,
        birth_date=date(1990, 1, 1),
        member_number=100321,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    second_user = User.objects.create_user(
        email="member-number-2@example.com",
        password="StrongPass123!",
        first_name="B",
        last_name="Two",
        role=User.ROLE_MEMBER,
    )
    second_profile = Profile.objects.create(
        user=second_user,
        birth_date=date(1991, 1, 1),
        member_number=None,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )

    second_profile.allocate_member_number()
    second_profile.refresh_from_db()

    assert first_profile.member_number == 100321
    assert second_profile.member_number == 100322


@pytest.mark.django_db
def test_profile_onboarding_complete_is_false_without_mandate(member_user):
    member_user.profile.sepa_mandate = None
    member_user.profile.save(update_fields=["sepa_mandate", "updated_at"])
    member_user.profile.sepa_mandates.update(is_active=False)

    assert member_user.profile.onboarding_complete is False


@pytest.mark.django_db
def test_profile_onboarding_complete_uses_active_mandate_relation(member_user):
    member_user.profile.sepa_mandate = None
    member_user.profile.save(update_fields=["sepa_mandate", "updated_at"])
    member_user.profile.sepa_mandates.create(
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Max Mustermann",
        mandate_reference="ALT-MANDATE-1",
        is_active=True,
    )

    assert member_user.profile.onboarding_complete is True


@pytest.mark.django_db
def test_profile_reset_limits_if_due_resets_daily_and_monthly(member_user):
    member_user.profile.daily_used = Decimal("12.50")
    member_user.profile.monthly_used = Decimal("42.00")
    member_user.profile.daily_counter_date = date(2026, 1, 1)
    member_user.profile.monthly_counter_key = "2026-01"
    member_user.profile.save(
        update_fields=["daily_used", "monthly_used", "daily_counter_date", "monthly_counter_key", "updated_at"]
    )

    member_user.profile.reset_limits_if_due(today=date(2026, 2, 1))
    member_user.profile.refresh_from_db()

    assert member_user.profile.daily_used == Decimal("0.00")
    assert member_user.profile.monthly_used == Decimal("0.00")
    assert member_user.profile.daily_counter_date == date(2026, 2, 1)
    assert member_user.profile.monthly_counter_key == "2026-02"


@pytest.mark.django_db
def test_verification_submission_has_required_documents_property(member_user):
    submission = VerificationSubmission.objects.create(
        profile=member_user.profile,
        status=VerificationSubmission.STATUS_DRAFT,
    )
    assert submission.has_required_documents is False

    submission.id_front_image = SimpleUploadedFile("front.jpg", b"front", content_type="image/jpeg")
    submission.id_back_image = SimpleUploadedFile("back.jpg", b"back", content_type="image/jpeg")
    submission.save(update_fields=["id_front_image", "id_back_image", "updated_at"])

    assert submission.has_required_documents is True
