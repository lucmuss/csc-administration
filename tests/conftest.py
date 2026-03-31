import os
from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone

os.environ.setdefault("USE_SQLITE_FOR_TESTS", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


@pytest.fixture
def member_user(db):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile
    from apps.participation.models import MemberEngagement

    user = User.objects.create_user(
        email="member@example.com",
        password="StrongPass123!",
        first_name="Max",
        last_name="Mustermann",
        role=User.ROLE_MEMBER,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100000,
        balance=Decimal("200.00"),
        desired_join_date=date(2026, 4, 1),
        street_address="Karl-Liebknecht-Strasse 9",
        postal_code="04107",
        city="Leipzig",
        phone="+4915112345678",
        bank_name="ING",
        account_holder_name="Max Mustermann",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        optional_newsletter_opt_in=True,
        registration_completed_at=timezone.now(),
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Max Mustermann",
        mandate_reference="CSC-FIXTURE-MEMBER",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    MemberEngagement.objects.create(profile=profile, registration_completed=True)
    return user
