from __future__ import annotations

from datetime import date
from time import sleep

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.db import IntegrityError

from apps.accounts.models import User
from apps.core.forms import SocialClubOpeningHourForm, SocialClubSettingsForm
from apps.core.models import ClubConfiguration, PublicDocument, SocialClub, SocialClubOpeningHour, SocialClubReview
from apps.members.models import Profile


@pytest.mark.django_db
def test_social_club_slug_is_unique_with_collision_suffix():
    c1 = SocialClub.objects.create(
        name="CSC Leipzig Süd",
        email="a@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+491",
        is_active=True,
        is_approved=True,
    )
    c2 = SocialClub.objects.create(
        name="CSC Leipzig Sud",
        email="b@example.com",
        street_address="B",
        postal_code="04109",
        city="Leipzig",
        phone="+492",
        is_active=True,
        is_approved=True,
    )

    assert c1.slug
    assert c2.slug
    assert c1.slug != c2.slug


@pytest.mark.django_db
def test_social_club_slug_fallback_for_special_characters():
    club = SocialClub.objects.create(
        name="!!!",
        email="fallback@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49555",
        is_active=True,
        is_approved=True,
    )

    assert club.slug == "social-club"


@pytest.mark.django_db
def test_social_club_slug_stays_unchanged_on_update_without_name_change():
    club = SocialClub.objects.create(
        name="CSC Stable Slug",
        email="stable@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49666",
        is_active=True,
        is_approved=True,
    )
    original_slug = club.slug

    club.city = "Berlin"
    club.save(update_fields=["city", "updated_at"])
    club.refresh_from_db()

    assert club.slug == original_slug


@pytest.mark.django_db
def test_social_club_gallery_images_returns_five_elements():
    club = SocialClub.objects.create(
        name="CSC Gallery",
        email="gallery@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49777",
        is_active=True,
        is_approved=True,
    )

    images = club.gallery_images

    assert len(images) == 5
    assert all(not image for image in images)


def test_social_club_has_all_16_federal_states_and_name_ordering():
    assert len(SocialClub.FEDERAL_STATE_CHOICES) == 16
    assert SocialClub._meta.ordering == ["name"]


@pytest.mark.django_db
def test_opening_hour_form_rejects_end_before_start():
    form = SocialClubOpeningHourForm(
        data={
            "weekday": SocialClubOpeningHour.WEEKDAY_MONDAY,
            "starts_at": "18:00",
            "ends_at": "14:00",
        }
    )
    assert form.is_valid() is False
    assert "Endzeit" in str(form.errors)


@pytest.mark.django_db
def test_social_club_opening_hour_model_string_and_ordering_and_cascade():
    club = SocialClub.objects.create(
        name="CSC Hours",
        email="hours@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49888",
        is_active=True,
        is_approved=True,
    )
    first = SocialClubOpeningHour.objects.create(social_club=club, weekday=2, starts_at="14:00", ends_at="18:00")
    second = SocialClubOpeningHour.objects.create(social_club=club, weekday=1, starts_at="10:00", ends_at="12:00")

    assert "CSC Hours" in str(first)
    assert "Mittwoch" in str(first)
    assert list(SocialClubOpeningHour.objects.values_list("id", flat=True)) == [second.id, first.id]

    club.delete()
    assert SocialClubOpeningHour.objects.count() == 0


@pytest.mark.django_db
def test_social_club_review_unique_per_user_and_club():
    club = SocialClub.objects.create(
        name="CSC Review Club",
        email="review@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+493",
        is_active=True,
        is_approved=True,
    )
    user = User.objects.create_user(
        email="review-user@example.com",
        password="StrongPass123!",
        first_name="Re",
        last_name="Viewer",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key="2026-04",
    )
    SocialClubReview.objects.create(social_club=club, user=user, rating=5)

    with pytest.raises(IntegrityError):
        SocialClubReview.objects.create(social_club=club, user=user, rating=4)


@pytest.mark.django_db
def test_social_club_review_check_constraint_for_rating_bounds():
    club = SocialClub.objects.create(
        name="CSC Rating Bounds",
        email="bounds@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49999",
        is_active=True,
        is_approved=True,
    )
    user = User.objects.create_user(
        email="rating-user@example.com",
        password="StrongPass123!",
        first_name="Re",
        last_name="Bounds",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key="2026-04",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            SocialClubReview.objects.create(social_club=club, user=user, rating=0)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            SocialClubReview.objects.create(social_club=club, user=user, rating=6)
    review = SocialClubReview.objects.create(social_club=club, user=user, rating=3)
    assert str(review) == f"{club.name} · {user.email} (3/5)"


@pytest.mark.django_db
def test_social_club_review_cascade_on_social_club_delete():
    club = SocialClub.objects.create(
        name="CSC Review Cascade",
        email="review-cascade@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49001",
        is_active=True,
        is_approved=True,
    )
    user = User.objects.create_user(
        email="review-cascade-user@example.com",
        password="StrongPass123!",
        first_name="Re",
        last_name="Cascade",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        monthly_counter_key="2026-04",
    )
    SocialClubReview.objects.create(social_club=club, user=user, rating=5)

    club.delete()
    assert SocialClubReview.objects.count() == 0


@pytest.mark.django_db
def test_club_configuration_behaves_like_singleton_and_updates_timestamp():
    first = ClubConfiguration.objects.create(club_name="Club A")
    first_updated_at = first.updated_at
    sleep(0.01)
    second = ClubConfiguration.objects.create(club_name="Club B")

    assert first.pk == 1
    assert second.pk == 1
    assert ClubConfiguration.objects.count() == 1
    stored = ClubConfiguration.objects.get(pk=1)
    assert stored.club_name == "Club B"
    assert stored.updated_at >= first_updated_at
    assert str(stored) == "Club B"

    stored.delete()
    assert ClubConfiguration.objects.count() == 0


@pytest.mark.django_db
def test_club_configuration_string_fallback_chain():
    config = ClubConfiguration.objects.create(app_name="")
    assert str(config) == "Club-Konfiguration"
    config.app_name = "App Name"
    config.club_name = ""
    config.save(update_fields=["app_name", "club_name", "updated_at"])
    config.refresh_from_db()
    assert str(config) == "App Name"


@pytest.mark.django_db
def test_public_document_file_properties_for_extensions():
    club = SocialClub.objects.create(
        name="CSC Docs",
        email="docs@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49002",
        is_active=True,
        is_approved=True,
    )
    pdf_doc = PublicDocument.objects.create(
        social_club=club,
        title="Satzung",
        file=SimpleUploadedFile("satzung.PDF", b"pdf", content_type="application/pdf"),
    )
    image_doc = PublicDocument.objects.create(
        social_club=club,
        title="Lageplan",
        file=SimpleUploadedFile("plan.png", b"img", content_type="image/png"),
    )
    binary_doc = PublicDocument.objects.create(
        social_club=club,
        title="Formular",
        file=SimpleUploadedFile("formular.docx", b"docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    )
    noext_doc = PublicDocument.objects.create(
        social_club=club,
        title="Ohne Endung",
        file=SimpleUploadedFile("ohneendung", b"x", content_type="application/octet-stream"),
    )

    assert pdf_doc.file_extension == "pdf"
    assert pdf_doc.file_badge == "PDF"
    assert pdf_doc.file_action_label == "PDF herunterladen"
    assert image_doc.file_action_label == "Datei ansehen"
    assert binary_doc.file_action_label == "Datei herunterladen"
    assert noext_doc.file_extension == ""
    assert noext_doc.file_badge == "Datei"


@pytest.mark.django_db
def test_public_document_default_public_and_social_club_cascade():
    club = SocialClub.objects.create(
        name="CSC Public Docs",
        email="public-docs@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+49003",
        is_active=True,
        is_approved=True,
    )
    doc = PublicDocument.objects.create(
        social_club=club,
        title="Infoblatt",
        file=SimpleUploadedFile("info.pdf", b"pdf", content_type="application/pdf"),
    )
    assert doc.is_public is True
    club.delete()
    assert PublicDocument.objects.count() == 0


@pytest.mark.django_db
def test_social_club_settings_form_splits_and_recombines_street_and_number():
    club = SocialClub.objects.create(
        name="CSC Adresse",
        email="adresse@example.com",
        street_address="Mannheimer Strasse 132a",
        postal_code="04109",
        city="Leipzig",
        phone="+49444",
        is_active=True,
        is_approved=True,
    )

    form = SocialClubSettingsForm(instance=club)
    assert form.initial.get("street_address") == "Mannheimer Strasse"
    assert form.initial.get("street_address_number") == "132a"

    form = SocialClubSettingsForm(
        data={
            "name": club.name,
            "public_description": "",
            "email": club.email,
            "phone": club.phone,
            "street_address": "Mannheimer Strasse",
            "street_address_number": "132",
            "postal_code": club.postal_code,
                "city": club.city,
                "federal_state": club.federal_state or SocialClub.BUNDESLAND_SN,
            "minimum_age": 21,
            "max_verified_members": 500,
            "admission_fee": "0.00",
            "monthly_membership_fee": "24.00",
            "club_iban": "",
            "club_bic": "",
            "stripe_account_id": "",
            "stripe_dashboard_url": "",
            "board_representatives": "",
            "register_entry": "",
            "register_court": "",
            "tax_number": "",
            "vat_id": "",
            "supervisory_authority": "",
            "content_responsible": "",
            "responsible_person": "",
            "language_notice": "",
            "legal_basis_notice": "",
            "retention_notice": "",
            "external_services_text": "",
            "prevention_officer_name": "",
            "prevention_notice": "",
            "instagram_url": "",
            "telegram_url": "",
            "whatsapp_url": "",
            "website": "",
            "support_email": "",
            "membership_email": "",
            "prevention_email": "",
            "finance_email": "",
            "privacy_contact": "",
            "data_protection_officer": "",
        },
        instance=club,
    )
    assert form.is_valid(), form.errors
    updated = form.save()
    assert updated.street_address == "Mannheimer Strasse 132"
