from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.members.forms import MemberProfileEditForm, MemberRegistrationForm


@pytest.fixture
def second_member_user(db):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile
    from apps.participation.models import MemberEngagement

    user = User.objects.create_user(
        email="othermember@example.com",
        password="StrongPass123!",
        first_name="Lara",
        last_name="Neufeld",
        role=User.ROLE_MEMBER,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1991, 5, 5),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100111,
        balance=Decimal("125.00"),
        desired_join_date=date(2026, 4, 1),
        street_address="Testweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+491701112233",
        bank_name="GLS Bank",
        account_holder_name="Lara Neufeld",
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
        monthly_used=Decimal("18.00"),
        last_activity=timezone.now(),
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Lara Neufeld",
        mandate_reference="CSC-FIXTURE-OTHER-MEMBER",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    MemberEngagement.objects.create(profile=profile, registration_completed=True)
    return user


@pytest.mark.django_db
def test_member_directory_hides_sensitive_fields_for_members(client, member_user, second_member_user):
    client.force_login(member_user)

    response = client.get(reverse("members:directory"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "125.00 EUR" not in html
    assert "18.00 g / 50 g" not in html
    assert "Verifiziert: Ja" in html


@pytest.mark.django_db
def test_member_profile_hides_private_fields_for_other_members(client, member_user, second_member_user):
    client.force_login(member_user)

    response = client.get(reverse("members:detail", args=[second_member_user.profile.id]))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "Bankverbindung und Lastschrift" not in html
    assert "Adresse und Vereinsangaben" not in html
    assert "125.00 EUR" not in html
    assert "18.00 g / 50 g" not in html
    assert "Letzte Aktivitaet" in html


@pytest.mark.django_db
def test_cutting_shop_card_does_not_render_thc_stat(client, member_user):
    from apps.inventory.models import Strain

    cutting = Strain.objects.create(
        name="Steckling: Orange Bud",
        product_type=Strain.PRODUCT_TYPE_CUTTING,
        thc=Decimal("0.00"),
        cbd=Decimal("0.00"),
        price=Decimal("5.00"),
        stock=Decimal("12.00"),
    )
    client.force_login(member_user)

    response = client.get(reverse("orders:shop") + "?type=cutting")

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert reverse("inventory:strain_detail", args=[cutting.id]) in html
    assert "Steckling: Orange Bud" in html
    assert "<span class=\"shop-card-compact__label\">THC</span>" not in html


@pytest.mark.django_db
def test_member_can_cancel_own_order_within_window(client, member_user):
    from apps.inventory.models import Strain
    from apps.orders.services import create_reserved_order, CartLine

    strain = Strain.objects.create(
        name="Blue Dream",
        thc=Decimal("20.00"),
        cbd=Decimal("0.20"),
        price=Decimal("8.00"),
        stock=Decimal("50.00"),
    )
    order = create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=strain.id, quantity=Decimal("2"))])
    client.force_login(member_user)

    response = client.post(reverse("orders:cancel", args=[order.id]))

    assert response.status_code == 302
    assert response.url == reverse("orders:list")
    assert member_user.orders.filter(id=order.id).exists() is False


@pytest.mark.django_db
def test_member_cannot_cancel_order_after_window(member_user):
    from apps.inventory.models import Strain
    from apps.orders.models import Order
    from apps.orders.services import create_reserved_order, member_cancel_reserved_order, CartLine

    strain = Strain.objects.create(
        name="Channel",
        thc=Decimal("18.00"),
        cbd=Decimal("0.10"),
        price=Decimal("7.00"),
        stock=Decimal("50.00"),
    )
    order = create_reserved_order(user=member_user, cart_lines=[CartLine(strain_id=strain.id, quantity=Decimal("2"))])
    Order.objects.filter(id=order.id).update(created_at=timezone.now() - timedelta(hours=30))
    order.refresh_from_db()

    with pytest.raises(ValidationError):
        member_cancel_reserved_order(order=order)


def test_registration_form_rejects_invalid_identity_fields():
    form = MemberRegistrationForm(
        data={
            "first_name": "Lu1",
            "last_name": "Mu",
            "email": "test@invalid",
            "birth_date": "1990-01-01",
            "password": "StrongPass123!",
        }
    )

    assert form.is_valid() is False
    assert "first_name" in form.errors
    assert "last_name" in form.errors
    assert "email" in form.errors


@pytest.mark.django_db
def test_profile_edit_form_validates_bank_fields(member_user):
    form = MemberProfileEditForm(
        profile=member_user.profile,
        data={
            "first_name": "Maximilian",
            "last_name": "Mustermann",
            "email": "max@example.com",
            "phone": "+4915112345678",
            "street_address": "Karl-Liebknecht-Strasse 9",
            "postal_code": "0410",
            "city": "Leipzig",
            "bank_name": "1",
            "account_holder_name": "Ma1",
            "iban": "DE123",
            "bic": "123",
            "optional_newsletter_opt_in": "True",
            "application_notes": "",
        },
    )

    assert form.is_valid() is False
    assert "postal_code" in form.errors
    assert "bank_name" in form.errors
    assert "account_holder_name" in form.errors
    assert "iban" in form.errors
    assert "bic" in form.errors
