from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.finance.models import UploadedInvoice
from apps.finance.services import (
    _best_invoice_reference,
    _best_total_amount,
    _build_invoice_title,
    _candidate_vendor_name,
    _extract_json_payload,
    _local_invoice_fallback,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Rechnungsnummer: ABC-2026-991", "ABC-2026-991"),
        ("invoice no INV-777", "INV-777"),
        ("Ref 123456", "123456"),
    ],
)
def test_best_invoice_reference_extracts_common_patterns(text, expected):
    assert _best_invoice_reference(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Gesamtbetrag 19,99 EUR", Decimal("19.99")),
        ("zu zahlen: 120.50", Decimal("120.50")),
        ("no amount here", Decimal("0.00")),
    ],
)
def test_best_total_amount_parses_keywords_and_fallback(text, expected):
    assert _best_total_amount(text) == expected


def test_candidate_vendor_name_skips_invoice_keywords():
    text = "Rechnung\nGesamt\nGreen Leaf GmbH\nMusterstrasse 5"
    assert _candidate_vendor_name(text) == "Green Leaf GmbH"


@pytest.mark.parametrize(
    "vendor,reference,issue_date,fallback,expected",
    [
        ("Vendor GmbH", "R-1", None, "file", "Vendor GmbH · Ref R-1"),
        ("Vendor GmbH", "", None, "file", "Vendor GmbH"),
        ("", "R-1", None, "file", "Rechnung R-1"),
        ("", "", None, "fallback-name", "fallback-name"),
    ],
)
def test_build_invoice_title_variants(vendor, reference, issue_date, fallback, expected):
    assert _build_invoice_title(vendor=vendor, reference=reference, issue_date=issue_date, fallback_name=fallback) == expected


def test_extract_json_payload_supports_fenced_json_block():
    raw = "```json\n{\"invoice_reference\":\"A-1\",\"amount_gross\":\"10.00\"}\n```"
    parsed = _extract_json_payload(raw)
    assert parsed["invoice_reference"] == "A-1"


@pytest.mark.django_db
def test_local_invoice_fallback_populates_missing_fields(member_user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    uploaded = UploadedInvoice.objects.create(
        title="",
        document=SimpleUploadedFile("invoice.txt", b"Green Leaf GmbH\nRechnungsnummer GL-2026-1\nGesamt 49,90 EUR", content_type="text/plain"),
        created_by=member_user,
    )

    updated = _local_invoice_fallback(uploaded, "Green Leaf GmbH\nRechnungsnummer GL-2026-1\nGesamt 49,90 EUR")

    assert updated.extraction_status == UploadedInvoice.EXTRACTION_SUCCESS
    assert updated.invoice_number == "GL-2026-1"
    assert updated.vendor_name == "Green Leaf GmbH"
    assert updated.amount_gross == Decimal("49.90")
    assert "local-fallback" == updated.ai_payload.get("source")
