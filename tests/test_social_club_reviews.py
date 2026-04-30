from datetime import date

import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.core.models import SocialClub, SocialClubReview
from apps.finance.models import SepaMandate
from apps.members.models import Profile


def _complete_onboarding(profile):
    profile.desired_join_date = date(2026, 5, 1)
    profile.street_address = "Teststrasse 1"
    profile.postal_code = "04109"
    profile.city = "Leipzig"
    profile.phone = "+491511111111"
    profile.bank_name = "Testbank"
    profile.account_holder_name = profile.user.full_name or profile.user.email
    profile.privacy_accepted = True
    profile.direct_debit_accepted = True
    profile.no_other_csc_membership = True
    profile.german_residence_confirmed = True
    profile.minimum_age_confirmed = True
    profile.id_document_confirmed = True
    profile.important_newsletter_opt_in = True
    profile.registration_completed_at = profile.created_at
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder=profile.account_holder_name,
        mandate_reference=f"TEST-REVIEW-{profile.user_id}",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save()


@pytest.mark.django_db
def test_verified_active_member_can_submit_review(client):
    club = SocialClub.objects.create(
        name="CSC Review Club",
        email="review@example.com",
        street_address="R1",
        postal_code="04109",
        city="Leipzig",
        phone="+49111",
        is_approved=True,
        is_active=True,
    )
    user = User.objects.create_user(
        email="review-member@example.com",
        password="StrongPass123!",
        first_name="Review",
        last_name="Member",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=300001,
        monthly_counter_key="2026-04",
    )
    _complete_onboarding(profile)

    client.force_login(user)
    response = client.post(
        reverse("core:social_club_review"),
        data={"rating": 4, "comment": "Sehr gute Organisation"},
        follow=True,
    )

    assert response.status_code == 200
    review = SocialClubReview.objects.get(user=user, social_club=club)
    assert review.rating == 4
    assert "gute Organisation" in review.comment


@pytest.mark.django_db
def test_unverified_member_cannot_submit_review(client):
    club = SocialClub.objects.create(
        name="CSC No Review",
        email="noreview@example.com",
        street_address="N1",
        postal_code="04109",
        city="Leipzig",
        phone="+49222",
        is_approved=True,
        is_active=True,
    )
    user = User.objects.create_user(
        email="noreview-member@example.com",
        password="StrongPass123!",
        first_name="No",
        last_name="Review",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        monthly_counter_key="2026-04",
    )
    _complete_onboarding(profile)

    client.force_login(user)
    response = client.get(reverse("core:social_club_review"), follow=True)

    assert response.status_code == 200
    assert not SocialClubReview.objects.filter(user=user, social_club=club).exists()


@pytest.mark.django_db
def test_member_cannot_submit_review_after_exit(client):
    club = SocialClub.objects.create(
        name="CSC Exit",
        email="exit@example.com",
        street_address="E1",
        postal_code="04109",
        city="Leipzig",
        phone="+49333",
        is_approved=True,
        is_active=True,
    )
    user = User.objects.create_user(
        email="exit-member@example.com",
        password="StrongPass123!",
        first_name="Exit",
        last_name="Member",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_REJECTED,
        is_verified=False,
        monthly_counter_key="2026-04",
    )
    _complete_onboarding(profile)

    client.force_login(user)
    response = client.post(reverse("core:social_club_review"), data={"rating": 1, "comment": "-"}, follow=True)

    assert response.status_code == 200
    assert not SocialClubReview.objects.filter(user=user, social_club=club).exists()
