from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from apps.core.models import SocialClub
from apps.members.models import Profile, VerificationSubmission


@pytest.fixture
def board_user(db):
    User = get_user_model()
    club = SocialClub.objects.create(
        name="CSC Board Club",
        email="boardclub@example.com",
        street_address="Boardweg 1",
        postal_code="04107",
        city="Leipzig",
        phone="+491511111111",
        is_active=True,
        is_approved=True,
    )
    user = User.objects.create_user(
        email="board@example.com",
        password="StrongPass123!",
        first_name="Bo",
        last_name="Ard",
        role=User.ROLE_BOARD,
        is_staff=True,
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1988, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100500,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    return user


@pytest.mark.django_db
def test_verification_detail_forbidden_for_regular_member(client, member_user):
    client.force_login(member_user)
    response = client.get(reverse("members:verification_detail", args=[member_user.profile.id]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_verification_submit_requires_both_required_images(client, member_user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    client.force_login(member_user)

    response = client.post(
        reverse("members:verification"),
        data={"id_front_image": SimpleUploadedFile("front.jpg", b"data", content_type="image/jpeg")},
    )

    assert response.status_code == 200
    assert "id_back_image" in response.context["form"].errors


@pytest.mark.django_db
def test_member_action_verify_rejects_cross_club_action(client, board_user):
    User = get_user_model()
    other_club = SocialClub.objects.create(
        name="CSC Other Club",
        email="other@example.com",
        street_address="Otherweg 2",
        postal_code="10115",
        city="Berlin",
        phone="+491522222222",
        is_active=True,
        is_approved=True,
    )
    foreign_member = User.objects.create_user(
        email="foreign@example.com",
        password="StrongPass123!",
        first_name="For",
        last_name="Eign",
        role=User.ROLE_MEMBER,
        social_club=other_club,
    )
    profile = Profile.objects.create(
        user=foreign_member,
        birth_date=date(1992, 2, 2),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )

    client.force_login(board_user)
    response = client.post(reverse("members:action", args=[profile.id]), data={"action": "verify", "confirm": "yes"})

    assert response.status_code == 302
    profile.refresh_from_db()
    assert profile.is_verified is False


@pytest.mark.django_db
def test_import_members_requires_email_mapping(client, board_user):
    client.force_login(board_user)
    session = client.session
    session["member_import_payload"] = {
        "headers": ["Vorname", "Nachname"],
        "preview_rows": [{"Vorname": "Max", "Nachname": "Mustermann"}],
        "raw_text": "Vorname,Nachname\nMax,Mustermann\n",
        "delimiter": ",",
    }
    session.save()

    response = client.post(
        reverse("members:import"),
        data={"action": "import", "mapping_0": "first_name", "mapping_1": "last_name"},
        follow=True,
    )

    assert response.status_code == 200
    assert "E-Mail-Adresse" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_import_members_creates_pending_unverified_member(client, board_user):
    client.force_login(board_user)
    session = client.session
    session["member_import_payload"] = {
        "headers": ["E-Mail-Adresse", "Geburtsdatum", "Vorname", "Nachname"],
        "preview_rows": [],
        "raw_text": "E-Mail-Adresse,Geburtsdatum,Vorname,Nachname\nnew.member@example.com,03.04.1990,New,Member\n",
        "delimiter": ",",
    }
    session.save()

    response = client.post(
        reverse("members:import"),
        data={
            "action": "import",
            "mapping_0": "email",
            "mapping_1": "birth_date",
            "mapping_2": "first_name",
            "mapping_3": "last_name",
        },
        follow=True,
    )

    assert response.status_code == 200
    imported = get_user_model().objects.get(email="new.member@example.com")
    imported_profile = imported.profile
    assert imported_profile.status == Profile.STATUS_PENDING
    assert imported_profile.is_verified is False


@pytest.mark.django_db
def test_verification_approve_sets_profile_active_and_submission_approved(client, board_user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    User = get_user_model()
    member = User.objects.create_user(
        email="verifyme@example.com",
        password="StrongPass123!",
        first_name="Veri",
        last_name="Fy",
        role=User.ROLE_MEMBER,
        social_club=board_user.social_club,
    )
    profile = Profile.objects.create(
        user=member,
        birth_date=date(1995, 5, 5),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    VerificationSubmission.objects.create(
        profile=profile,
        status=VerificationSubmission.STATUS_SUBMITTED,
        id_front_image=SimpleUploadedFile("front.jpg", b"front", content_type="image/jpeg"),
        id_back_image=SimpleUploadedFile("back.jpg", b"back", content_type="image/jpeg"),
        submitted_at=timezone.now(),
    )

    client.force_login(board_user)
    response = client.post(
        reverse("members:verification_detail", args=[profile.id]),
        data={"action": "approve", "admin_notes": "looks good"},
        follow=True,
    )

    assert response.status_code == 200
    profile.refresh_from_db()
    profile.verification_submission.refresh_from_db()
    assert profile.is_verified is True
    assert profile.status == Profile.STATUS_ACTIVE
    assert profile.verification_submission.status == VerificationSubmission.STATUS_APPROVED
