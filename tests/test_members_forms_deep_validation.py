from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.members.forms import (
    MemberOnboardingForm,
    MemberProfileEditForm,
    MemberRegistrationForm,
    VerificationSubmissionForm,
)
from apps.members.models import VerificationSubmission


@pytest.mark.django_db
def test_member_registration_form_filters_social_clubs_by_federal_state():
    from apps.core.models import SocialClub

    sn = SocialClub.objects.create(
        name="CSC Sachsen",
        email="sn@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+491",
        federal_state="SN",
        is_active=True,
        is_approved=True,
    )
    SocialClub.objects.create(
        name="CSC Bayern",
        email="by@example.com",
        street_address="B",
        postal_code="80331",
        city="Muenchen",
        phone="+492",
        federal_state="BY",
        is_active=True,
        is_approved=True,
    )

    form = MemberRegistrationForm(federal_state="SN")
    ids = list(form.fields["social_club"].queryset.values_list("id", flat=True))
    assert sn.id in ids
    assert len(ids) == 1


@pytest.mark.django_db
def test_member_registration_form_rejects_underage(settings):
    settings.MEMBER_MINIMUM_AGE = 21
    form = MemberRegistrationForm(
        data={
            "email": "underage@example.com",
            "first_name": "Jung",
            "last_name": "Mitglied",
            "birth_date": (date.today() - timedelta(days=365 * 18)).isoformat(),
            "password": "StrongPass123!",
        }
    )
    assert form.is_valid() is False
    assert "birth_date" in form.errors


@pytest.mark.django_db
def test_member_registration_form_uses_social_club_specific_minimum_age(settings):
    from apps.core.models import SocialClub

    settings.MEMBER_MINIMUM_AGE = 21
    club = SocialClub.objects.create(
        name="CSC Berlin 18+",
        email="berlin18@example.com",
        street_address="Teststrasse 1",
        postal_code="10115",
        city="Berlin",
        phone="+4930",
        federal_state="BE",
        minimum_age=18,
        is_active=True,
        is_approved=True,
    )

    form = MemberRegistrationForm(
        data={
            "social_club": str(club.id),
            "email": "young-adult@example.com",
            "first_name": "Jana",
            "last_name": "Beispiel",
            "birth_date": (date.today() - timedelta(days=365 * 19)).isoformat(),
            "password": "StrongPass123!",
            "accept_terms": "on",
        }
    )
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_member_registration_form_requires_terms_acceptance():
    form = MemberRegistrationForm(
        data={
            "email": "terms-required@example.com",
            "first_name": "Erika",
            "last_name": "Muster",
            "birth_date": "1990-01-01",
            "password": "StrongPass123!",
        }
    )
    assert form.is_valid() is False
    assert "accept_terms" in form.errors


@pytest.mark.django_db
def test_member_onboarding_form_rejects_future_join_date_for_today_guard(member_user):
    form = MemberOnboardingForm(
        profile=member_user.profile,
        data={
            "desired_join_date": (date.today() - timedelta(days=1)).isoformat(),
            "street_address": "Testweg 1",
            "postal_code": "04109",
            "city": "Leipzig",
            "phone": "+491701112233",
            "iban": "DE44500105175407324931",
            "bic": "INGDDEFFXXX",
            "bank_name": "ING",
            "account_holder_name": "Max Mustermann",
            "privacy_accepted": "on",
            "direct_debit_accepted": "on",
            "no_other_csc_membership": "on",
            "german_residence_confirmed": "on",
            "minimum_age_confirmed": "on",
            "id_document_confirmed": "on",
            "important_newsletter_opt_in": "on",
            "optional_newsletter_opt_in": "True",
            "application_notes": "",
        },
    )
    assert form.is_valid() is False
    assert "desired_join_date" in form.errors


@pytest.mark.django_db
def test_member_profile_edit_form_accepts_english_placeholder(member_user):
    form = MemberProfileEditForm(
        profile=member_user.profile,
        data={
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "member@example.com",
            "phone": "+4915112345678",
            "street_address": "Karl-Liebknecht-Strasse 9",
            "postal_code": "04107",
            "city": "Leipzig",
            "bank_name": "ING",
            "account_holder_name": "Max Mustermann",
            "iban": "DE44500105175407324931",
            "bic": "INGDDEFFXXX",
            "optional_newsletter_opt_in": "True",
            "preferred_language": "en",
            "payment_method_preference": "sepa",
            "application_notes": "",
        },
    )
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_verification_submission_form_rejects_non_image_for_required_id_files(member_user):
    submission = VerificationSubmission.objects.create(profile=member_user.profile)
    form = VerificationSubmissionForm(
        instance=submission,
        data={},
        files={
            "id_front_image": SimpleUploadedFile("front.pdf", b"%PDF-1.4", content_type="application/pdf"),
            "id_back_image": SimpleUploadedFile("back.jpg", b"img", content_type="image/jpeg"),
        },
    )
    assert form.is_valid() is False
    assert "id_front_image" in form.errors


@pytest.mark.django_db
def test_verification_submission_form_allows_optional_docs_empty(member_user):
    submission = VerificationSubmission.objects.create(profile=member_user.profile)
    form = VerificationSubmissionForm(
        instance=submission,
        data={},
        files={
            "id_front_image": SimpleUploadedFile("front.jpg", b"img", content_type="image/jpeg"),
            "id_back_image": SimpleUploadedFile("back.jpg", b"img", content_type="image/jpeg"),
        },
    )
    assert form.is_valid(), form.errors
