from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.members.models import Profile, VerificationSubmission
from apps.core.models import SocialClub
from apps.finance.models import BalanceTransaction


@pytest.mark.django_db
@pytest.mark.parametrize("field_name", ["id_front_image", "id_back_image"])
def test_verification_upload_rejects_files_over_5mb(client, member_user, settings, tmp_path, field_name):
    settings.MEDIA_ROOT = tmp_path
    client.force_login(member_user)

    large_file = SimpleUploadedFile("big.jpg", b"0" * (5 * 1024 * 1024 + 1), content_type="image/jpeg")
    other_file = SimpleUploadedFile("ok.jpg", b"ok", content_type="image/jpeg")
    payload = {
        "id_front_image": large_file if field_name == "id_front_image" else other_file,
        "id_back_image": large_file if field_name == "id_back_image" else other_file,
    }

    response = client.post(reverse("members:verification"), data=payload)
    assert response.status_code == 200
    assert "maximal 5 MB" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_member_can_submit_verification_documents(client, member_user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    member_user.profile.is_verified = False
    member_user.profile.status = Profile.STATUS_PENDING
    member_user.profile.save(update_fields=["is_verified", "status", "updated_at"])

    client.force_login(member_user)
    response = client.post(
        reverse("members:verification"),
        data={
            "id_front_image": SimpleUploadedFile("front.jpg", b"front", content_type="image/jpeg"),
            "id_back_image": SimpleUploadedFile("back.jpg", b"back", content_type="image/jpeg"),
            "membership_application_document": SimpleUploadedFile("aufnahme.pdf", b"pdf", content_type="application/pdf"),
        },
        follow=True,
    )
    assert response.status_code == 200
    submission = VerificationSubmission.objects.get(profile=member_user.profile)
    assert submission.status == VerificationSubmission.STATUS_SUBMITTED
    assert submission.id_front_image.name
    assert submission.id_back_image.name


@pytest.mark.django_db
def test_board_can_approve_verification_submission(client, member_user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    User = get_user_model()
    board = User.objects.create_user(
        email="board-verify@example.com",
        password="StrongPass123!",
        first_name="Board",
        last_name="User",
        role=User.ROLE_BOARD,
        is_staff=True,
        is_superuser=True,
    )
    Profile.objects.create(
        user=board,
        birth_date=date(1985, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100123,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )

    member_user.profile.is_verified = False
    member_user.profile.status = Profile.STATUS_PENDING
    member_user.profile.save(update_fields=["is_verified", "status", "updated_at"])
    VerificationSubmission.objects.create(
        profile=member_user.profile,
        status=VerificationSubmission.STATUS_SUBMITTED,
        id_front_image=SimpleUploadedFile("front.jpg", b"front", content_type="image/jpeg"),
        id_back_image=SimpleUploadedFile("back.jpg", b"back", content_type="image/jpeg"),
        submitted_at=timezone.now(),
    )

    client.force_login(board)
    response = client.post(
        reverse("members:verification_detail", args=[member_user.profile.id]),
        data={"action": "approve", "admin_notes": "ok"},
        follow=True,
    )
    assert response.status_code == 200
    member_user.profile.refresh_from_db()
    submission = member_user.profile.verification_submission
    assert member_user.profile.is_verified is True
    assert member_user.profile.status == Profile.STATUS_ACTIVE
    assert submission.status == VerificationSubmission.STATUS_APPROVED
    assert submission.approved_by_id == board.id


@pytest.mark.django_db
def test_admission_fee_created_once_on_verification_approval(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    User = get_user_model()
    club = SocialClub.objects.create(
        name="CSC Fee Club",
        email="feeclub@example.com",
        street_address="Feeweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49111",
        is_active=True,
        is_approved=True,
        admission_fee="20.00",
    )
    board = User.objects.create_user(
        email="board-fee@example.com",
        password="StrongPass123!",
        first_name="Board",
        last_name="Fee",
        role=User.ROLE_BOARD,
        is_staff=True,
        social_club=club,
    )
    Profile.objects.create(
        user=board,
        birth_date=date(1985, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100323,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    member = User.objects.create_user(
        email="member-fee@example.com",
        password="StrongPass123!",
        first_name="Mina",
        last_name="Mitglied",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    member_profile = Profile.objects.create(
        user=member,
        birth_date=date(1992, 1, 1),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        desired_join_date=timezone.localdate(),
        street_address="Teststrasse 1",
        postal_code="04109",
        city="Leipzig",
        phone="+4917000000",
        bank_name="Testbank",
        account_holder_name="Mina Mitglied",
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
        account_holder="Mina Mitglied",
        mandate_reference="MANDATE-FEE-1",
        is_active=True,
    )
    VerificationSubmission.objects.create(
        profile=member_profile,
        status=VerificationSubmission.STATUS_SUBMITTED,
        id_front_image=SimpleUploadedFile("front.jpg", b"front", content_type="image/jpeg"),
        id_back_image=SimpleUploadedFile("back.jpg", b"back", content_type="image/jpeg"),
        submitted_at=timezone.now(),
    )

    client.force_login(board)
    response = client.post(
        reverse("members:verification_detail", args=[member_profile.id]),
        data={"action": "approve", "admin_notes": "ok"},
        follow=True,
    )

    assert response.status_code == 200
    fee_transactions = BalanceTransaction.objects.filter(profile=member_profile, reference=f"admission-fee-{member_profile.id}")
    assert fee_transactions.count() == 1
    assert str(fee_transactions.first().amount) == "20.00"


@pytest.mark.django_db
def test_board_cannot_approve_verification_when_club_capacity_reached(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    User = get_user_model()
    club = SocialClub.objects.create(
        name="CSC Capacity",
        email="capacity@example.com",
        street_address="Clubweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49111",
        is_active=True,
        is_approved=True,
        max_verified_members=1,
    )
    board = User.objects.create_user(
        email="board-capacity@example.com",
        password="StrongPass123!",
        first_name="Board",
        last_name="User",
        role=User.ROLE_BOARD,
        is_staff=True,
        social_club=club,
    )
    Profile.objects.create(
        user=board,
        birth_date=date(1985, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100223,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    verified_member = User.objects.create_user(
        email="already-verified@example.com",
        password="StrongPass123!",
        first_name="Erika",
        last_name="Verifiziert",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    Profile.objects.create(
        user=verified_member,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100224,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    pending_member = User.objects.create_user(
        email="pending-capacity@example.com",
        password="StrongPass123!",
        first_name="Pia",
        last_name="Pending",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    pending_profile = Profile.objects.create(
        user=pending_member,
        birth_date=date(1992, 1, 1),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    VerificationSubmission.objects.create(
        profile=pending_profile,
        status=VerificationSubmission.STATUS_SUBMITTED,
        id_front_image=SimpleUploadedFile("front.jpg", b"front", content_type="image/jpeg"),
        id_back_image=SimpleUploadedFile("back.jpg", b"back", content_type="image/jpeg"),
        submitted_at=timezone.now(),
    )

    client.force_login(board)
    response = client.post(
        reverse("members:verification_detail", args=[pending_profile.id]),
        data={"action": "approve", "admin_notes": "ok"},
        follow=True,
    )

    assert response.status_code == 200
    pending_profile.refresh_from_db()
    pending_submission = pending_profile.verification_submission
    assert pending_profile.is_verified is False
    assert pending_profile.status == Profile.STATUS_PENDING
    assert pending_submission.status == VerificationSubmission.STATUS_SUBMITTED


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_verification_reminder_command_sends_for_unverified_member(member_user):
    member_user.profile.is_verified = False
    member_user.profile.status = Profile.STATUS_PENDING
    member_user.profile.registration_completed_at = timezone.now()
    member_user.profile.verification_reminder_sent_at = None
    member_user.profile.save(
        update_fields=["is_verified", "status", "registration_completed_at", "verification_reminder_sent_at", "updated_at"]
    )

    call_command("send_verification_reminders")
    member_user.profile.refresh_from_db()

    assert len(mail.outbox) == 1
    assert member_user.email in mail.outbox[0].to
    assert "/members/verification/" in mail.outbox[0].body
    assert member_user.profile.verification_reminder_sent_at is not None
