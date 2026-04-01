from datetime import date

import pytest
from django.urls import reverse


@pytest.fixture
def board_user(db):
    from apps.accounts.models import User
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="club-board@example.com",
        password="StrongPass123!",
        first_name="Franka",
        last_name="Vorstand",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1986, 5, 5),
        status="active",
        is_verified=True,
        member_number=777001,
        desired_join_date=date(2026, 4, 1),
        street_address="Testweg 1",
        postal_code="04107",
        city="Leipzig",
        phone="+491700000000",
        bank_name="GLS",
        account_holder_name="Franka Vorstand",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    return user


@pytest.mark.django_db
def test_board_can_update_club_configuration_and_imprint_uses_it(client, board_user):
    client.force_login(board_user)

    response = client.post(
        reverse("core:club_settings"),
        data={
            "app_name": "Club Suite",
            "app_tagline": "Mehr-Club Verwaltung",
            "app_description": "Mandantenfaehige Verwaltungssoftware",
            "club_name": "Cannabis Social Club Test e.V.",
            "club_slogan": "Anbauverein in Teststadt",
            "club_contact_email": "info@test-club.eu",
            "club_contact_phone": "+49 176 1111111",
            "club_contact_address": "Postfach 1\n04109 Teststadt",
            "club_board_representatives": "Alex Beispiel",
            "club_register_entry": "Amtsgericht Test VR 1234",
            "club_register_court": "Amtsgericht Test",
            "club_tax_number": "123/456/789",
            "club_vat_id": "DE999999999",
            "club_supervisory_authority": "Stadt Teststadt",
            "club_content_responsible": "Alex Beispiel",
            "club_responsible_person": "Alex Beispiel\nTestverein",
            "club_membership_email": "mitglied@test-club.eu",
            "club_prevention_email": "praevention@test-club.eu",
            "club_finance_email": "finanzen@test-club.eu",
            "club_privacy_contact": "datenschutz@test-club.eu",
            "club_data_protection_officer": "Dana Datenschutz",
            "club_language_notice": "Wir bearbeiten Anfragen auf Deutsch.",
            "club_legal_basis_notice": "Rechtsgrundlagen Test",
            "club_retention_notice": "Aufbewahrung Test",
            "club_external_services_text": "Stripe\nOpenRouter",
            "prevention_officer_name": "Lisa Praevention",
            "prevention_notice": "Bitte wenden Sie sich an Lisa Praevention.",
            "instagram_url": "https://instagram.com/testclub",
            "telegram_url": "https://t.me/testclub",
            "whatsapp_url": "https://wa.me/4917612345678",
            "email_signature_text": "Testclub\ninfo@test-club.eu",
            "email_signature_html": "<strong>Testclub</strong><br>info@test-club.eu",
        },
    )

    assert response.status_code == 302

    imprint = client.get(reverse("core:imprint"))
    html = imprint.content.decode("utf-8")
    assert "Cannabis Social Club Test e.V." in html
    assert "Lisa Praevention" in html
    assert "https://instagram.com/testclub" in html
    assert "https://t.me/testclub" in html
    assert "https://wa.me/4917612345678" in html


@pytest.mark.django_db
def test_club_email_context_uses_database_configuration(board_user):
    from apps.accounts.emails import _club_email_context
    from apps.core.models import ClubConfiguration

    ClubConfiguration.objects.create(
        club_name="Custom Club",
        club_contact_email="info@custom.club",
        email_signature_text="Custom Club\ninfo@custom.club",
    )

    context = _club_email_context()

    assert context["club_name"] == "Custom Club"
    assert context["club_contact_email"] == "info@custom.club"
    assert "Custom Club" in context["club_email_signature_text"]


@pytest.mark.django_db
def test_membership_documents_include_prevention_and_membership_contacts():
    import io

    from pypdf import PdfReader

    from apps.accounts.models import User
    from apps.core.models import ClubConfiguration
    from apps.finance.models import SepaMandate
    from apps.members.documents import membership_document_attachments
    from apps.members.models import Profile

    ClubConfiguration.objects.create(
        club_name="Custom Club",
        club_membership_email="mitglied@custom.club",
        club_prevention_email="praevention@custom.club",
        prevention_officer_name="Lina Schutz",
    )
    user = User.objects.create_user(email="pdfmember@example.com", password="StrongPass123!", role=User.ROLE_MEMBER)
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status="active",
        is_verified=True,
        desired_join_date=date(2026, 4, 1),
        street_address="Musterweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+491511111111",
        bank_name="GLS",
        account_holder_name="Pdf Member",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Pdf Member",
        mandate_reference="CSC-PDF-MEMBER",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])

    attachments = membership_document_attachments(profile)
    text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(attachments[0][1])).pages)

    assert "mitglied@custom.club" in text
    assert "praevention@custom.club" in text
    assert "Lina Schutz" in text
