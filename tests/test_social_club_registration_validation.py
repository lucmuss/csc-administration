from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from apps.core.forms import SocialClubRegistrationForm
from apps.core.models import SocialClub


def _base_form_data(**overrides):
    data = {
        "name": "Cannabis Social Club Leipzig Sued e.V.",
        "email": "kontakt@example-club.de",
        "phone": "+49 341 1234567",
        "street_address": "Mannheimer Strasse",
        "street_address_number": "132B",
        "postal_code": "04209",
        "city": "Leipzig",
        "federal_state": SocialClub.BUNDESLAND_SN,
        "minimum_age": 21,
        "website": "https://example.com",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
@override_settings(CLUB_REGISTRATION_VALIDATE_WEBSITE_REACHABILITY=False)
def test_social_club_registration_form_accepts_valid_data():
    form = SocialClubRegistrationForm(data=_base_form_data())
    assert form.is_valid(), form.errors


@pytest.mark.django_db
@override_settings(CLUB_REGISTRATION_VALIDATE_WEBSITE_REACHABILITY=False)
def test_social_club_registration_form_rejects_invalid_phone():
    form = SocialClubRegistrationForm(data=_base_form_data(phone="abc"))
    assert not form.is_valid()
    assert "phone" in form.errors


@pytest.mark.django_db
@override_settings(CLUB_REGISTRATION_VALIDATE_WEBSITE_REACHABILITY=False)
def test_social_club_registration_form_rejects_invalid_house_number():
    form = SocialClubRegistrationForm(data=_base_form_data(street_address_number="Hausnummer 12"))
    assert not form.is_valid()
    assert "street_address_number" in form.errors


@pytest.mark.django_db
@override_settings(CLUB_REGISTRATION_VALIDATE_WEBSITE_REACHABILITY=False)
def test_social_club_registration_form_rejects_invalid_postal_code():
    form = SocialClubRegistrationForm(data=_base_form_data(postal_code="12A45"))
    assert not form.is_valid()
    assert "postal_code" in form.errors


@pytest.mark.django_db
@override_settings(CLUB_REGISTRATION_VALIDATE_WEBSITE_REACHABILITY=False)
def test_social_club_registration_form_rejects_too_short_city():
    form = SocialClubRegistrationForm(data=_base_form_data(city="AB"))
    assert not form.is_valid()
    assert "city" in form.errors


@pytest.mark.django_db
@override_settings(CLUB_REGISTRATION_VALIDATE_WEBSITE_REACHABILITY=False)
def test_social_club_registration_form_requires_federal_state():
    form = SocialClubRegistrationForm(data=_base_form_data(federal_state=""))
    assert not form.is_valid()
    assert "federal_state" in form.errors


@pytest.mark.django_db
@override_settings(CLUB_REGISTRATION_VALIDATE_WEBSITE_REACHABILITY=True)
def test_social_club_registration_form_checks_website_reachability():
    mocked_response = MagicMock()
    mocked_response.__enter__.return_value.status = 200
    mocked_response.__exit__.return_value = False
    with patch("apps.core.forms.urlopen", return_value=mocked_response):
        form = SocialClubRegistrationForm(data=_base_form_data(website="https://example.com"))
        assert form.is_valid(), form.errors


@pytest.mark.django_db
@override_settings(CLUB_REGISTRATION_VALIDATE_WEBSITE_REACHABILITY=True)
def test_social_club_registration_form_rejects_unreachable_website():
    with patch("apps.core.forms.urlopen", side_effect=Exception("boom")):
        form = SocialClubRegistrationForm(data=_base_form_data(website="https://example.com"))
        assert not form.is_valid()
        assert "website" in form.errors
