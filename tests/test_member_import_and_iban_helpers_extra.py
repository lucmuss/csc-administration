from __future__ import annotations

import json
from urllib.error import URLError

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from apps.members.forms import _lookup_iban_bank_data, _validate_bic, _validate_iban
from apps.members.views import (
    _normalize_import_header,
    _parse_csv_upload,
    _parse_import_bool,
    _parse_import_date,
    _sanitize_search_query,
    _suggest_import_mapping,
)


pytestmark = pytest.mark.django_db


class _FakeHTTPResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_validate_iban_accepts_valid_value_and_normalizes_spaces():
    assert _validate_iban("DE44 5001 0517 5407 3249 31") == "DE44500105175407324931"


def test_validate_iban_rejects_invalid_format():
    with pytest.raises(ValidationError):
        _validate_iban("DE12")


def test_validate_iban_rejects_invalid_checksum():
    with pytest.raises(ValidationError):
        _validate_iban("DE44500105175407324930")


def test_validate_bic_accepts_valid_value_and_normalizes_case():
    assert _validate_bic("ingddeffxxx") == "INGDDEFFXXX"


def test_validate_bic_rejects_invalid_value():
    with pytest.raises(ValidationError):
        _validate_bic("12")


@override_settings(IBAN_API_VALIDATION_ENABLED=False, IBAN_API_VALIDATION_ENDPOINT="https://iban.example/{iban}")
def test_lookup_iban_bank_data_returns_empty_when_api_disabled():
    assert _lookup_iban_bank_data("DE44500105175407324931") == {}


@override_settings(IBAN_API_VALIDATION_ENABLED=True, IBAN_API_VALIDATION_ENDPOINT="")
def test_lookup_iban_bank_data_returns_empty_when_endpoint_missing():
    assert _lookup_iban_bank_data("DE44500105175407324931") == {}


@override_settings(IBAN_API_VALIDATION_ENABLED=True, IBAN_API_VALIDATION_ENDPOINT="https://iban.example/{iban}")
def test_lookup_iban_bank_data_raises_when_api_marks_iban_invalid(monkeypatch):
    monkeypatch.setattr(
        "apps.members.forms.urlopen",
        lambda request, timeout=5: _FakeHTTPResponse({"valid": False}),
    )
    with pytest.raises(ValidationError):
        _lookup_iban_bank_data("DE44500105175407324931")


@override_settings(IBAN_API_VALIDATION_ENABLED=True, IBAN_API_VALIDATION_ENDPOINT="https://iban.example/{iban}")
def test_lookup_iban_bank_data_returns_bank_payload(monkeypatch):
    monkeypatch.setattr(
        "apps.members.forms.urlopen",
        lambda request, timeout=5: _FakeHTTPResponse(
            {
                "valid": True,
                "bankData": {
                    "bic": "INGDDEFFXXX",
                    "name": "ING",
                },
            }
        ),
    )

    result = _lookup_iban_bank_data("DE44500105175407324931")
    assert result == {"bic": "INGDDEFFXXX", "bank_name": "ING"}


@override_settings(IBAN_API_VALIDATION_ENABLED=True, IBAN_API_VALIDATION_ENDPOINT="https://iban.example/{iban}")
def test_lookup_iban_bank_data_returns_empty_on_timeout_or_transport_error(monkeypatch):
    def _raise_timeout(request, timeout=5):
        raise URLError("timeout")

    monkeypatch.setattr("apps.members.forms.urlopen", _raise_timeout)
    assert _lookup_iban_bank_data("DE44500105175407324931") == {}


def test_import_helpers_sanitize_header_mapping_date_and_bool():
    assert _sanitize_search_query("  Erika  <script>alert(1)</script>  ") == "Erika scriptalert1script"
    assert _normalize_import_header("  E-Mail-Adresse  ") == "emailadresse"
    assert _suggest_import_mapping("E-Mail-Adresse") == "email"
    assert _parse_import_date("03.04.2026").isoformat() == "2026-04-03"
    assert _parse_import_date("2026-04-03").isoformat() == "2026-04-03"
    assert _parse_import_date("invalid") is None
    assert _parse_import_bool("ja") is True
    assert _parse_import_bool("yes") is True
    assert _parse_import_bool("1") is True
    assert _parse_import_bool("true") is True
    assert _parse_import_bool("nein") is False


def test_parse_csv_upload_supports_comma_semicolon_and_utf8_bom():
    csv_comma = SimpleUploadedFile(
        "members-comma.csv",
        b"email,first_name,last_name\nalice@example.com,Alice,Tester\n",
        content_type="text/csv",
    )
    headers_comma, rows_comma, text_comma = _parse_csv_upload(csv_comma)
    assert headers_comma == ["email", "first_name", "last_name"]
    assert rows_comma[0]["email"] == "alice@example.com"
    assert "alice@example.com" in text_comma

    csv_semicolon = SimpleUploadedFile(
        "members-semicolon.csv",
        "email;first_name;last_name\nbob@example.com;Bob;Tester\n".encode("utf-8"),
        content_type="text/csv",
    )
    headers_semicolon, rows_semicolon, _ = _parse_csv_upload(csv_semicolon)
    assert headers_semicolon == ["email", "first_name", "last_name"]
    assert rows_semicolon[0]["email"] == "bob@example.com"

    csv_bom = SimpleUploadedFile(
        "members-bom.csv",
        b"\xef\xbb\xbfemail,first_name,last_name\ncarol@example.com,Carol,Tester\n",
        content_type="text/csv",
    )
    headers_bom, rows_bom, _ = _parse_csv_upload(csv_bom)
    assert headers_bom == ["email", "first_name", "last_name"]
    assert rows_bom[0]["email"] == "carol@example.com"


def test_parse_csv_upload_handles_empty_file():
    uploaded = SimpleUploadedFile("empty.csv", b"", content_type="text/csv")
    headers, rows, raw_text = _parse_csv_upload(uploaded)
    assert headers == []
    assert rows == []
    assert raw_text == ""


def test_iban_lookup_requires_value(client, member_user):
    client.force_login(member_user)
    response = client.get(reverse("members:iban_lookup"))
    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert payload["valid"] is False


def test_iban_lookup_returns_invalid_for_bad_iban(client, member_user):
    client.force_login(member_user)
    response = client.get(reverse("members:iban_lookup"), {"iban": "BAD"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["valid"] is False


def test_iban_lookup_returns_bank_data_when_available(client, member_user, monkeypatch):
    client.force_login(member_user)

    monkeypatch.setattr(
        "apps.members.views._lookup_iban_bank_data",
        lambda iban: {"bic": "INGDDEFFXXX", "bank_name": "ING"},
    )

    response = client.get(reverse("members:iban_lookup"), {"iban": "DE44500105175407324931"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["valid"] is True
    assert payload["matches"] == 1
    assert payload["bic"] == "INGDDEFFXXX"
    assert payload["bank_name"] == "ING"
