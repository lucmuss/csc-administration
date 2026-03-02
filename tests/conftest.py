import os
from datetime import date
from decimal import Decimal

import pytest

os.environ.setdefault("USE_SQLITE_FOR_TESTS", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


@pytest.fixture
def member_user(db):
    from apps.accounts.models import User
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
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    MemberEngagement.objects.create(profile=profile)
    return user
