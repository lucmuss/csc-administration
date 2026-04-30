from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.core.models import SocialClub
from apps.finance.models import BalanceTopUp, BalanceTransaction
from apps.finance.services import (
    apply_admission_fee_if_needed,
    apply_monthly_membership_credits,
    create_stripe_checkout_for_topup,
    create_stripe_setup_session_for_member,
    finalize_stripe_setup_session_for_member,
    finalize_stripe_topup,
)
from apps.members.models import Profile


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.django_db
@override_settings(STRIPE_SECRET_KEY="")
def test_create_setup_session_returns_empty_without_stripe(member_user):
    url = create_stripe_setup_session_for_member(
        user=member_user,
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )
    assert url == ""


@pytest.mark.django_db
@override_settings(STRIPE_SECRET_KEY="sk_test_123")
def test_create_setup_session_returns_checkout_url_on_success(member_user, monkeypatch):
    def _fake_open(request, timeout=20):
        return _FakeResponse({"url": "https://checkout.stripe.test/setup/abc"})

    monkeypatch.setattr("apps.finance.services.urllib.request.urlopen", _fake_open)

    url = create_stripe_setup_session_for_member(
        user=member_user,
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )
    assert url == "https://checkout.stripe.test/setup/abc"


@pytest.mark.django_db
@override_settings(STRIPE_SECRET_KEY="sk_test_123")
def test_finalize_setup_session_persists_customer_and_payment_method(member_user, monkeypatch):
    payload = {
        "customer": "cus_123",
        "setup_intent": {"payment_method": {"id": "pm_456"}},
    }

    monkeypatch.setattr("apps.finance.services.urllib.request.urlopen", lambda request, timeout=20: _FakeResponse(payload))

    ok = finalize_stripe_setup_session_for_member(user=member_user, session_id="cs_test_1")

    member_user.profile.refresh_from_db()
    assert ok is True
    assert member_user.profile.stripe_customer_id == "cus_123"
    assert member_user.profile.stripe_payment_method_id == "pm_456"
    assert member_user.profile.payment_method_preference == Profile.PAYMENT_METHOD_STRIPE_CARD


@pytest.mark.django_db
@override_settings(STRIPE_SECRET_KEY="sk_test_123")
def test_finalize_setup_session_returns_false_for_incomplete_payload(member_user, monkeypatch):
    monkeypatch.setattr("apps.finance.services.urllib.request.urlopen", lambda request, timeout=20: _FakeResponse({"customer": ""}))
    ok = finalize_stripe_setup_session_for_member(user=member_user, session_id="cs_test_2")
    assert ok is False


@pytest.mark.django_db
@override_settings(STRIPE_SECRET_KEY="")
def test_create_topup_marks_failed_when_stripe_not_configured(member_user):
    topup = create_stripe_checkout_for_topup(
        user=member_user,
        amount=Decimal("25.00"),
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )
    assert topup.status == BalanceTopUp.STATUS_FAILED
    assert "nicht konfiguriert" in topup.failure_reason.lower()


@pytest.mark.django_db
@override_settings(STRIPE_SECRET_KEY="sk_test_123")
def test_finalize_topup_paid_adds_balance_transaction(member_user, monkeypatch):
    topup = BalanceTopUp.objects.create(profile=member_user.profile, amount=Decimal("30.00"), checkout_session_id="cs_paid")

    monkeypatch.setattr(
        "apps.finance.services.urllib.request.urlopen",
        lambda request, timeout=20: _FakeResponse({"payment_status": "paid"}),
    )

    finalized = finalize_stripe_topup(topup=topup)
    finalized.refresh_from_db()

    assert finalized.status == BalanceTopUp.STATUS_COMPLETED
    assert BalanceTransaction.objects.filter(
        profile=member_user.profile,
        kind=BalanceTransaction.KIND_TOPUP,
        reference="stripe-session-cs_paid",
    ).exists()


@pytest.mark.django_db
@override_settings(STRIPE_SECRET_KEY="sk_test_123")
def test_monthly_membership_credits_for_stripe_member(member_user, monkeypatch):
    club = SocialClub.objects.create(
        name="CSC Stripe Fees",
        email="club@example.com",
        street_address="Musterweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49111111111",
        is_active=True,
        is_approved=True,
        monthly_membership_fee=Decimal("24.00"),
    )
    member_user.social_club = club
    member_user.save(update_fields=["social_club"])

    profile = member_user.profile
    profile.payment_method_preference = Profile.PAYMENT_METHOD_STRIPE_CARD
    profile.stripe_customer_id = "cus_aaa"
    profile.stripe_payment_method_id = "pm_bbb"
    profile.is_verified = True
    profile.status = Profile.STATUS_ACTIVE
    profile.save(
        update_fields=[
            "payment_method_preference",
            "stripe_customer_id",
            "stripe_payment_method_id",
            "is_verified",
            "status",
            "updated_at",
        ]
    )

    monkeypatch.setattr("apps.finance.services._stripe_offsession_charge", lambda **kwargs: True)

    credited = apply_monthly_membership_credits(today=date(2026, 4, 15))
    credited_again = apply_monthly_membership_credits(today=date(2026, 4, 15))

    assert credited == 1
    assert credited_again == 0
    assert BalanceTransaction.objects.filter(
        profile=profile,
        reference=f"membership-fee-2026-04-{profile.id}",
    ).count() == 1


@pytest.mark.django_db
def test_admission_fee_not_created_when_member_not_eligible(member_user):
    club = SocialClub.objects.create(
        name="CSC Admission Guard",
        email="club2@example.com",
        street_address="Musterweg 2",
        postal_code="04109",
        city="Leipzig",
        phone="+49222222222",
        is_active=True,
        is_approved=True,
        admission_fee=Decimal("20.00"),
    )
    member_user.social_club = club
    member_user.save(update_fields=["social_club"])

    profile = member_user.profile
    profile.is_verified = False
    profile.status = Profile.STATUS_PENDING
    profile.save(update_fields=["is_verified", "status", "updated_at"])

    created = apply_admission_fee_if_needed(profile)

    assert created is False
    assert not BalanceTransaction.objects.filter(profile=profile, reference=f"admission-fee-{profile.id}").exists()
