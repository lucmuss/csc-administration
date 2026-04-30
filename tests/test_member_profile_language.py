import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_member_can_store_preferred_language_and_session(client, member_user):
    client.force_login(member_user)
    response = client.post(
        reverse("members:profile"),
        data={
            "first_name": member_user.first_name,
            "last_name": member_user.last_name,
            "email": member_user.email,
            "phone": member_user.profile.phone or "+4917000000",
            "street_address": member_user.profile.street_address or "Teststrasse 1",
            "postal_code": member_user.profile.postal_code or "04109",
            "city": member_user.profile.city or "Leipzig",
            "bank_name": member_user.profile.bank_name or "Testbank",
            "account_holder_name": member_user.profile.account_holder_name or member_user.full_name or "Test Mitglied",
            "iban": "DE89370400440532013000",
            "bic": "COBADEFFXXX",
            "optional_newsletter_opt_in": "False",
            "preferred_language": "en",
            "application_notes": member_user.profile.application_notes or "",
        },
        follow=True,
    )

    assert response.status_code == 200
    member_user.profile.refresh_from_db()
    assert member_user.profile.preferred_language == "en"
    assert client.session.get("django_language") == "en"
