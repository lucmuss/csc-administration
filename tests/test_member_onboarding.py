from datetime import timedelta

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.members.forms import MemberOnboardingForm, MemberProfileEditForm, MemberRegistrationForm


@pytest.fixture(autouse=True)
def _enforce_onboarding_redirect_settings(settings):
    settings.ENFORCE_LOGIN_ONBOARDING_REDIRECT_IN_TESTS = True
    settings.ENFORCE_ONBOARDING_REDIRECT_IN_TESTS = True


@pytest.mark.django_db
def test_registration_creates_incomplete_onboarding_state(client):
    from apps.accounts.models import User
    from apps.core.models import SocialClub
    from apps.members.models import Profile

    club = SocialClub.objects.create(
        name="CSC Onboarding Club",
        email="onboarding-club@example.com",
        street_address="Testweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+491700000000",
        federal_state=SocialClub.BUNDESLAND_SN,
        is_active=True,
        is_approved=True,
    )
    User.objects.create_user(
        email="board@example.com",
        password="StrongPass123!",
        first_name="Bea",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
        social_club=club,
    )

    response = client.post(
        reverse("members:register"),
        data={
            "first_name": "Erika",
            "last_name": "Muster",
            "email": "erika@example.com",
            "birth_date": "1990-01-01",
            "password": "StrongPass123!",
            "federal_state": SocialClub.BUNDESLAND_SN,
            "social_club": club.id,
        },
    )

    profile = Profile.objects.select_related("engagement").get(user__email="erika@example.com")
    assert response.status_code == 302
    assert profile.engagement.registration_completed is False
    assert profile.engagement.registration_deadline is not None


@pytest.mark.django_db
def test_first_login_redirects_member_to_onboarding(client):
    from apps.accounts.models import User

    user = User.objects.create_user(
        email="newmember@example.com",
        password="StrongPass123!",
        first_name="Nina",
        last_name="Neu",
        role=User.ROLE_MEMBER,
    )
    from apps.members.models import Profile
    from apps.participation.models import MemberEngagement

    profile = Profile.objects.create(
        user=user,
        birth_date="1990-01-01",
        status=Profile.STATUS_PENDING,
        monthly_counter_key="2026-03",
    )
    MemberEngagement.objects.create(profile=profile, registration_completed=False)

    response = client.post(
        reverse("accounts:login"),
        data={"username": user.email, "password": "StrongPass123!"},
    )

    assert response.status_code == 302
    assert response.url == reverse("members:onboarding")


@pytest.mark.django_db
def test_first_login_redirects_board_to_onboarding(client):
    from apps.accounts.models import User
    from apps.members.models import Profile
    from apps.participation.models import MemberEngagement

    user = User.objects.create_user(
        email="board2@example.com",
        password="StrongPass123!",
        first_name="Bea",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date="1990-01-01",
        status=Profile.STATUS_ACTIVE,
        monthly_counter_key="2026-03",
    )
    MemberEngagement.objects.create(profile=profile, registration_completed=False)

    response = client.post(
        reverse("accounts:login"),
        data={"username": user.email, "password": "StrongPass123!"},
    )

    assert response.status_code == 302
    assert response.url == reverse("members:onboarding")


@pytest.mark.django_db
def test_incomplete_member_is_redirected_to_onboarding(client, member_user):
    member_user.profile.registration_completed_at = None
    member_user.profile.save(update_fields=["registration_completed_at", "updated_at"])
    client.force_login(member_user)

    response = client.get(reverse("core:dashboard"))

    assert response.status_code == 302
    assert response.url == reverse("members:onboarding")


@pytest.mark.django_db
def test_incomplete_staff_is_redirected_to_onboarding(client):
    from apps.accounts.models import User
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="staff@example.com",
        password="StrongPass123!",
        first_name="Sara",
        last_name="Staff",
        role=User.ROLE_STAFF,
        is_staff=True,
    )
    Profile.objects.create(
        user=user,
        birth_date="1990-01-01",
        status=Profile.STATUS_ACTIVE,
        monthly_counter_key="2026-03",
    )
    client.force_login(user)

    response = client.get(reverse("core:dashboard"))

    assert response.status_code == 302
    assert response.url == reverse("members:onboarding")


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_onboarding_form_saves_profile_and_mandate(client, member_user):
    from apps.finance.models import SepaMandate
    from apps.messaging.models import EmailGroup, EmailGroupMember

    member_user.profile.registration_completed_at = None
    member_user.profile.sepa_mandate = None
    member_user.profile.save(update_fields=["registration_completed_at", "sepa_mandate", "updated_at"])
    client.force_login(member_user)

    desired_join_date = (timezone.localdate() + timedelta(days=7)).isoformat()
    response = client.post(
        reverse("members:onboarding"),
        data={
            "desired_join_date": desired_join_date,
            "street_address": "Karl-Liebknecht-Strasse 9",
            "postal_code": "04107",
            "city": "Leipzig",
            "phone": "+4915112345678",
            "iban": "DE44500105175407324931",
            "bic": "INGDDEFFXXX",
            "bank_name": "ING",
            "account_holder_name": "Max Mustermann",
            "privacy_accepted": "on",
            "direct_debit_accepted": "on",
            "no_other_csc_membership": "on",
            "german_residence_confirmed": "on",
            "minimum_age_confirmed": "on",
            "id_document_confirmed": "on",
            "important_newsletter_opt_in": "on",
            "optional_newsletter_opt_in": "True",
            "application_notes": "Bitte Unterlagen per E-Mail zusaetzlich bestaetigen.",
        },
    )

    member_user.profile.refresh_from_db()
    member_user.profile.engagement.refresh_from_db()
    mandate = SepaMandate.objects.get(profile=member_user.profile)
    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")
    assert member_user.profile.street_address == "Karl-Liebknecht-Strasse 9"
    assert member_user.profile.bank_name == "ING"
    assert member_user.profile.account_holder_name == "Max Mustermann"
    assert member_user.profile.registration_completed_at is not None
    assert member_user.profile.onboarding_complete is True
    assert member_user.profile.engagement.registration_completed is True
    assert mandate.iban == "DE44500105175407324931"
    important_group = EmailGroup.objects.get(name="Wichtige Vereinsinfos")
    marketing_group = EmailGroup.objects.get(name="Preislisten und Angebote")
    assert EmailGroupMember.objects.filter(group=important_group, member=member_user.profile).exists()
    assert EmailGroupMember.objects.filter(group=marketing_group, member=member_user.profile).exists()
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [member_user.email]
    assert len(mail.outbox[0].attachments) == 3
    filenames = {attachment[0] for attachment in mail.outbox[0].attachments}
    assert "Aufnahmeantrag.pdf" in filenames
    assert "SEPA-Lastschriftmandat.pdf" in filenames
    assert "Mitgliederausweis.pdf" not in filenames


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_onboarding_form_allows_board_without_membership_documents(client):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile
    from apps.participation.models import MemberEngagement

    user = User.objects.create_user(
        email="board-onboarding@example.com",
        password="StrongPass123!",
        first_name="Berta",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date="1990-01-01",
        status=Profile.STATUS_ACTIVE,
        monthly_counter_key="2026-03",
    )
    profile.registration_completed_at = None
    profile.sepa_mandate = None
    profile.save(update_fields=["registration_completed_at", "sepa_mandate", "updated_at"])
    MemberEngagement.objects.update_or_create(profile=profile, defaults={"registration_completed": False})
    client.force_login(user)

    desired_join_date = (timezone.localdate() + timedelta(days=7)).isoformat()
    response = client.post(
        reverse("members:onboarding"),
        data={
            "desired_join_date": desired_join_date,
            "street_address": "Karl-Liebknecht-Strasse 9",
            "postal_code": "04107",
            "city": "Leipzig",
            "phone": "+4915112345678",
            "iban": "DE44500105175407324931",
            "bic": "INGDDEFFXXX",
            "bank_name": "ING",
            "account_holder_name": "Berta Board",
            "privacy_accepted": "on",
            "direct_debit_accepted": "on",
            "no_other_csc_membership": "on",
            "german_residence_confirmed": "on",
            "minimum_age_confirmed": "on",
            "id_document_confirmed": "on",
            "important_newsletter_opt_in": "on",
            "optional_newsletter_opt_in": "True",
            "application_notes": "Board Onboarding",
        },
    )

    profile.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")
    assert profile.onboarding_complete is True
    assert SepaMandate.objects.filter(profile=profile, is_active=True).exists()
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_completed_member_can_reach_dashboard(client, member_user):
    from apps.finance.models import SepaMandate

    mandate = SepaMandate.objects.create(
        profile=member_user.profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Max Mustermann",
        mandate_reference="CSC-TEST-COMPLETE",
        is_active=True,
    )
    member_user.profile.desired_join_date = member_user.profile.desired_join_date or member_user.profile.birth_date.replace(year=2026, month=4, day=1)
    member_user.profile.street_address = "Karl-Liebknecht-Strasse 9"
    member_user.profile.postal_code = "04107"
    member_user.profile.city = "Leipzig"
    member_user.profile.phone = "+4915112345678"
    member_user.profile.bank_name = "ING"
    member_user.profile.account_holder_name = "Max Mustermann"
    member_user.profile.privacy_accepted = True
    member_user.profile.direct_debit_accepted = True
    member_user.profile.no_other_csc_membership = True
    member_user.profile.german_residence_confirmed = True
    member_user.profile.minimum_age_confirmed = True
    member_user.profile.id_document_confirmed = True
    member_user.profile.important_newsletter_opt_in = True
    member_user.profile.registration_completed_at = member_user.profile.created_at
    member_user.profile.sepa_mandate = mandate
    member_user.profile.save()
    client.force_login(member_user)

    response = client.get(reverse("core:dashboard"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_verified_member_can_download_member_card_pdf(client, member_user):
    member_user.profile.is_verified = True
    member_user.profile.member_number = 555001
    member_user.profile.save(update_fields=["is_verified", "member_number", "updated_at"])
    client.force_login(member_user)

    response = client.get(reverse("members:member_card_pdf"))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert "Mitgliederausweis.pdf" in response["Content-Disposition"]


@pytest.mark.django_db
def test_registration_and_onboarding_forms_use_styled_inputs(member_user):
    registration_form = MemberRegistrationForm()
    onboarding_form = MemberOnboardingForm(profile=member_user.profile)
    profile_form = MemberProfileEditForm(profile=member_user.profile)

    assert "form-input" in registration_form.fields["email"].widget.attrs["class"]
    assert registration_form.fields["password"].widget.attrs["autocomplete"] == "new-password"
    assert registration_form.fields["birth_date"].widget.input_type == "date"
    assert registration_form.fields["birth_date"].widget.attrs["min"] == "1920-01-01"
    assert "max" in registration_form.fields["birth_date"].widget.attrs
    assert "form-input" in onboarding_form.fields["street_address"].widget.attrs["class"]
    assert "form-input" in onboarding_form.fields["application_notes"].widget.attrs["class"]
    assert "form-checkbox" in onboarding_form.fields["privacy_accepted"].widget.attrs["class"]
    assert "form-input" in profile_form.fields["iban"].widget.attrs["class"]


@pytest.mark.django_db
@override_settings(MEMBER_MINIMUM_AGE=18)
def test_registration_respects_configured_minimum_age():
    from apps.core.models import SocialClub

    club = SocialClub.objects.filter(is_active=True, is_approved=True).order_by("id").first()
    if club is None:
        club = SocialClub.objects.create(
            name="CSC Age Test",
            email="age-test@example.com",
            street_address="Testweg 1",
            postal_code="04109",
            city="Leipzig",
            phone="+491700000000",
            federal_state=SocialClub.BUNDESLAND_SN,
            is_active=True,
            is_approved=True,
        )
    club.minimum_age = 18
    club.save(update_fields=["minimum_age", "updated_at"])
    form = MemberRegistrationForm(
        data={
            "first_name": "Erika",
            "last_name": "Muster",
            "email": "erika2@example.com",
            "birth_date": "2008-01-01",
            "password": "StrongPass123!",
            "social_club": club.id,
        }
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_onboarding_form_defaults_join_date_to_first_day_of_next_month(member_user):
    member_user.profile.desired_join_date = None
    member_user.profile.save(update_fields=["desired_join_date", "updated_at"])
    onboarding_form = MemberOnboardingForm(profile=member_user.profile)

    assert onboarding_form.fields["desired_join_date"].initial.day == 1


@pytest.mark.django_db
def test_profile_edit_updates_member_and_messaging_preferences(client, member_user):
    from apps.finance.models import SepaMandate
    from apps.messaging.models import EmailGroupMember

    mandate = SepaMandate.objects.create(
        profile=member_user.profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Max Mustermann",
        mandate_reference="CSC-TEST-PROFILE",
        is_active=True,
    )
    member_user.profile.sepa_mandate = mandate
    member_user.profile.desired_join_date = member_user.profile.birth_date.replace(year=2026, month=4, day=1)
    member_user.profile.street_address = "Karl-Liebknecht-Strasse 9"
    member_user.profile.postal_code = "04107"
    member_user.profile.city = "Leipzig"
    member_user.profile.phone = "+4915112345678"
    member_user.profile.bank_name = "ING"
    member_user.profile.account_holder_name = "Max Mustermann"
    member_user.profile.privacy_accepted = True
    member_user.profile.direct_debit_accepted = True
    member_user.profile.no_other_csc_membership = True
    member_user.profile.german_residence_confirmed = True
    member_user.profile.minimum_age_confirmed = True
    member_user.profile.id_document_confirmed = True
    member_user.profile.important_newsletter_opt_in = True
    member_user.profile.registration_completed_at = member_user.profile.created_at
    member_user.profile.save()
    client.force_login(member_user)

    response = client.post(
        reverse("members:profile"),
        data={
            "first_name": "Mila",
            "last_name": "Mitglied",
            "email": "mila@example.com",
            "phone": "+491701112233",
            "street_address": "Neue Strasse 5",
            "postal_code": "04109",
            "city": "Leipzig",
            "bank_name": "GLS",
            "account_holder_name": "Mila Mitglied",
            "iban": "DE12500105170648489890",
                "bic": "GENODEM1GLS",
                "optional_newsletter_opt_in": "False",
                "preferred_language": "de",
                "payment_method_preference": "sepa",
                "application_notes": "Bitte auf neue Mailadresse umstellen.",
            },
        )

    member_user.refresh_from_db()
    member_user.profile.refresh_from_db()
    mandate.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("members:profile")
    assert member_user.first_name == "Mila"
    assert member_user.email == "mila@example.com"
    assert member_user.profile.bank_name == "GLS"
    assert mandate.iban == "DE12500105170648489890"
    assert EmailGroupMember.objects.filter(group__name="Preislisten und Angebote", member=member_user.profile).exists() is False
