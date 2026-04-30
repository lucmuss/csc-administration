from __future__ import annotations

from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.core.club import ACTIVE_FEDERAL_STATE_COOKIE, ACTIVE_SOCIAL_CLUB_COOKIE
from apps.core.models import SocialClub
from apps.members.models import Profile
from apps.finance.models import SepaMandate


@pytest.fixture
def board_user(db):
    club = SocialClub.objects.create(
        name="Board Club",
        email="boardclub@example.com",
        street_address="Clubweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+491111",
        is_active=True,
        is_approved=True,
    )
    user = User.objects.create_user(
        email="board-flow@example.com",
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
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    return user


@pytest.mark.django_db
def test_switch_social_club_rejects_foreign_club_for_non_superuser(client, board_user):
    foreign = SocialClub.objects.create(
        name="Foreign Club",
        email="foreign@example.com",
        street_address="Fremdweg 5",
        postal_code="10115",
        city="Berlin",
        phone="+491212",
        is_active=True,
        is_approved=True,
    )

    client.force_login(board_user)
    response = client.post(
        reverse("core:social_club_switch"),
        data={"social_club_id": foreign.id, "next": reverse("core:dashboard")},
        follow=True,
    )

    assert response.status_code == 200
    assert board_user.social_club_id != foreign.id


@pytest.mark.django_db
def test_switch_social_club_sets_cookie_for_superuser(client):
    club = SocialClub.objects.create(
        name="Cookie Club",
        email="cookie@example.com",
        street_address="Cookieweg 5",
        postal_code="04109",
        city="Leipzig",
        phone="+491313",
        is_active=True,
        is_approved=True,
    )
    superuser = User.objects.create_superuser(
        email="super-cookie@example.com",
        password="StrongPass123!",
        first_name="Sup",
        last_name="Er",
    )

    client.force_login(superuser)
    response = client.post(
        reverse("core:social_club_switch"),
        data={"social_club_id": club.id, "next": reverse("core:dashboard")},
    )

    assert response.status_code == 302
    assert ACTIVE_SOCIAL_CLUB_COOKIE in response.cookies


@pytest.mark.django_db
def test_switch_federal_state_resets_invalid_value(client):
    response = client.post(
        reverse("core:social_club_state_switch"),
        data={"federal_state": "SN", "next": reverse("core:social_club_regional_list")},
    )
    assert response.status_code == 302
    assert ACTIVE_FEDERAL_STATE_COOKIE in response.cookies

    response2 = client.post(
        reverse("core:social_club_state_switch"),
        data={"federal_state": "", "next": reverse("core:social_club_regional_list")},
    )
    assert response2.status_code == 302


@pytest.mark.django_db
def test_social_club_review_requires_verified_member(client):
    club = SocialClub.objects.create(
        name="Review Guard Club",
        email="rg@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+491414",
        is_active=True,
        is_approved=True,
    )
    user = User.objects.create_user(
        email="review-guard@example.com",
        password="StrongPass123!",
        first_name="Rev",
        last_name="Guard",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        desired_join_date=timezone.localdate(),
        street_address="Testweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+4917000001",
        bank_name="Testbank",
        account_holder_name="Rev Guard",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        registration_completed_at=timezone.now(),
        monthly_counter_key="2026-04",
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Rev Guard",
        mandate_reference="MANDATE-REVIEW-GUARD",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])

    client.force_login(user)
    response = client.get(reverse("core:social_club_review"))

    assert response.status_code == 302
    assert response.url == reverse("members:profile")


@pytest.mark.django_db
def test_social_club_review_allows_verified_member_to_submit(client):
    club = SocialClub.objects.create(
        name="Review Open Club",
        email="ro@example.com",
        street_address="A",
        postal_code="04109",
        city="Leipzig",
        phone="+491515",
        is_active=True,
        is_approved=True,
    )
    user = User.objects.create_user(
        email="review-open@example.com",
        password="StrongPass123!",
        first_name="Rev",
        last_name="Open",
        role=User.ROLE_MEMBER,
        social_club=club,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        desired_join_date=timezone.localdate(),
        street_address="Testweg 2",
        postal_code="04109",
        city="Leipzig",
        phone="+4917000002",
        bank_name="Testbank",
        account_holder_name="Rev Open",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        registration_completed_at=timezone.now(),
        monthly_counter_key="2026-04",
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Rev Open",
        mandate_reference="MANDATE-REVIEW-OPEN",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])

    client.force_login(user)
    response = client.post(
        reverse("core:social_club_review"),
        data={"rating": 4, "comment": "Gute Organisation"},
        follow=True,
    )

    assert response.status_code == 200
    assert "gespeichert" in response.content.decode("utf-8")
