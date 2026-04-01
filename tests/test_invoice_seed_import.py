from pathlib import Path
from datetime import date
from decimal import Decimal
import base64
import io
import json

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image


@pytest.fixture
def board_user(db):
    from apps.accounts.models import User
    from apps.finance.models import SepaMandate
    from apps.members.models import Profile

    user = User.objects.create_user(
        email="invoice-seed-board@example.com",
        password="StrongPass123!",
        first_name="Ina",
        last_name="Board",
        role=User.ROLE_BOARD,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1988, 4, 4),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=101900,
        desired_join_date=date(2026, 4, 1),
        street_address="Seedweg 4",
        postal_code="04107",
        city="Leipzig",
        phone="+4917612345000",
        bank_name="GLS",
        account_holder_name="Ina Board",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        registration_completed_at=timezone.now(),
        monthly_counter_key=date.today().strftime("%Y-%m"),
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE12500105170648489890",
        bic="GENODEM1GLS",
        account_holder="Ina Board",
        mandate_reference="CSC-FIXTURE-INVOICE-SEED",
        is_active=True,
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


@pytest.mark.django_db
def test_seed_invoice_archive_imports_temp_files(tmp_path, board_user, settings):
    from apps.finance.models import UploadedInvoice

    invoice_dir = tmp_path / "invoices"
    invoice_dir.mkdir(parents=True, exist_ok=True)
    (invoice_dir / "strom-april.txt").write_text(
        "Rechnung RE-2026-001\n02.04.2026\nGesamt 49,90 EUR\n",
        encoding="utf-8",
    )
    settings.MEDIA_ROOT = tmp_path / "media"

    call_command("seed_invoice_archive", directory=str(invoice_dir))

    uploaded = UploadedInvoice.objects.get(title="strom april")
    assert uploaded.invoice_number == "RE-2026-001"
    assert uploaded.amount_gross == Decimal("49.90")
    assert uploaded.document.name.endswith("strom-april.txt")


@pytest.mark.django_db
def test_real_invoice_directory_can_be_seeded_when_present(board_user):
    from apps.finance.models import UploadedInvoice

    invoice_dir = Path(settings.BASE_DIR) / "data" / "invoices"
    supported_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt"}
    supported_files = [item for item in invoice_dir.iterdir() if item.is_file() and item.suffix.lower() in supported_suffixes] if invoice_dir.exists() else []
    if not supported_files:
        pytest.skip("No invoice fixtures present in data/invoices yet.")

    call_command("seed_invoice_archive", directory=str(invoice_dir))

    file_count = len(supported_files)
    assert UploadedInvoice.objects.count() == file_count
    assert UploadedInvoice.objects.exclude(document="").count() == file_count

    imported_names = {Path(item.document.name).name for item in UploadedInvoice.objects.all()}
    expected_names = {item.name for item in supported_files}
    assert imported_names == expected_names

    for uploaded in UploadedInvoice.objects.all():
        assert uploaded.document.name
        assert uploaded.extraction_status in {
            UploadedInvoice.EXTRACTION_SUCCESS,
            UploadedInvoice.EXTRACTION_FAILED,
        }
        assert isinstance(uploaded.ai_payload, dict)
        assert uploaded.ai_payload
        assert uploaded.ai_payload.get("document_name")


@pytest.mark.django_db
def test_invoice_image_is_normalized_and_sent_to_model(client, board_user, settings, monkeypatch):
    from apps.finance.models import UploadedInvoice
    from apps.finance.services import analyze_uploaded_invoice

    settings.OPENROUTER_API_KEY = "test-key"
    settings.OPENROUTER_MODEL = "Qwen/Qwen3.5-27B"

    image_buffer = io.BytesIO()
    Image.new("RGBA", (120, 80), color=(255, 255, 255, 255)).save(image_buffer, format="WEBP")
    image_upload = SimpleUploadedFile("receipt.webp", image_buffer.getvalue(), content_type="image/webp")
    uploaded = UploadedInvoice.objects.create(
        title="Foto Rechnung",
        direction=UploadedInvoice.DIRECTION_INCOMING,
        document=image_upload,
        created_by=board_user,
        assigned_to=board_user,
    )

    captured = {}

    class _DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "invoice_number": "IMG-2026-001",
                                        "vendor_name": "Foto Test",
                                        "customer_name": "CSC",
                                        "issue_date": "2026-04-01",
                                        "due_date": "",
                                        "amount_net": "12.00",
                                        "amount_tax": "0.00",
                                        "amount_gross": "12.00",
                                        "currency": "EUR",
                                        "summary": "Bildrechnung erkannt",
                                    }
                                )
                            }
                        }
                    ]
                }
            ).encode("utf-8")

    def _fake_urlopen(request, timeout=0):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _DummyResponse()

    monkeypatch.setattr("apps.finance.services.urllib.request.urlopen", _fake_urlopen)

    analyze_uploaded_invoice(uploaded)
    uploaded.refresh_from_db()

    image_content = captured["body"]["messages"][0]["content"][1]
    assert image_content["type"] == "image_url"
    assert image_content["image_url"]["url"].startswith("data:image/png;base64,")
    base64.b64decode(image_content["image_url"]["url"].split(",", 1)[1])
    assert uploaded.extraction_status == UploadedInvoice.EXTRACTION_SUCCESS
    assert uploaded.invoice_number == "IMG-2026-001"
