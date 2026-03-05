"""E2E Test Fixtures für CSC-Administration"""
import os
from datetime import date, timedelta
from decimal import Decimal

import pytest

os.environ.setdefault("USE_SQLITE_FOR_TESTS", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


@pytest.fixture
def member_user(db):
    """Standard-Mitglied für Tests"""
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


@pytest.fixture
def staff_user(db):
    """Mitarbeiter für Tests"""
    from apps.accounts.models import User
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="staff@example.com",
        password="StrongPass123!",
        first_name="Anna",
        last_name="Mitarbeiterin",
        role=User.ROLE_STAFF,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1985, 5, 15),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100001,
    )
    return user


@pytest.fixture
def board_user(db):
    """Vorstand für Tests"""
    from apps.accounts.models import User
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="board@example.com",
        password="StrongPass123!",
        first_name="Vor",
        last_name="Stand",
        role=User.ROLE_BOARD,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1980, 3, 10),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100002,
    )
    return user


@pytest.fixture
def pending_member(db):
    """Mitglied mit pending Status"""
    from apps.accounts.models import User
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="pending@example.com",
        password="StrongPass123!",
        first_name="Pending",
        last_name="User",
        role=User.ROLE_MEMBER,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1995, 8, 20),
        status=Profile.STATUS_PENDING,
        is_verified=False,
        member_number=100003,
    )
    return user


@pytest.fixture
def strain(db):
    """Test-Sorte"""
    from apps.inventory.models import Strain

    return Strain.objects.create(
        name="Orange Bud",
        slug="orange-bud",
        thc_content=Decimal("18.00"),
        cbd_content=Decimal("0.50"),
        price_per_gram=Decimal("10.00"),
    )


@pytest.fixture
def batch(db, strain):
    """Test-Charge"""
    from apps.inventory.models import Batch

    return Batch.objects.create(
        strain=strain,
        batch_number="240301-OB",
        harvest_date=date.today(),
        total_harvested_grams=Decimal("3000.00"),
        available_grams=Decimal("2847.00"),
        price_per_gram=Decimal("10.00"),
        status=Batch.STATUS_AVAILABLE,
    )


@pytest.fixture
def email_group(db, member_user):
    """Test-E-Mail-Gruppe"""
    from apps.messaging.models import EmailGroup

    group = EmailGroup.objects.create(
        name="Test Gruppe",
        description="Eine Test-Gruppe",
    )
    group.members.add(member_user)
    return group


@pytest.fixture
def mass_email_draft(db, board_user):
    """Test-Massen-E-Mail als Draft"""
    from apps.messaging.models import MassEmail

    return MassEmail.objects.create(
        subject="Test E-Mail",
        content="Hallo {{ first_name }}",
        recipient_type=MassEmail.RECIPIENT_ALL,
        status=MassEmail.STATUS_DRAFT,
        created_by=board_user,
    )


@pytest.fixture
def invoice(db, member_user):
    """Test-Rechnung"""
    from apps.finance.models import Invoice

    return Invoice.objects.create(
        profile=member_user.profile,
        invoice_number="INV-TEST-001",
        amount=Decimal("49.90"),
        due_date=date.today(),
        status=Invoice.STATUS_OPEN,
    )


@pytest.fixture
def sepa_mandate(db, member_user):
    """Test-SEPA-Mandat"""
    from apps.finance.models import SepaMandate

    return SepaMandate.objects.create(
        profile=member_user.profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Max Mustermann",
        mandate_reference="CSC-100000-001",
        is_active=True,
    )
