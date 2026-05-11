from __future__ import annotations

from base64 import b64encode
from datetime import date
from difflib import SequenceMatcher
import json
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone


def _file_to_data_url(uploaded_file) -> str:
    content_type = getattr(uploaded_file, "content_type", "") or "image/jpeg"
    raw = uploaded_file.read()
    uploaded_file.seek(0)
    encoded = b64encode(raw).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _normalize_name(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _name_similarity(a: str, b: str) -> float:
    left = _normalize_name(a)
    right = _normalize_name(b)
    if not left or not right:
        return 0.0
    return round(SequenceMatcher(None, left, right).ratio() * 100, 2)


def _birth_date_similarity(extracted_birth_date: str, profile_birth_date: date) -> float:
    if not extracted_birth_date:
        return 0.0
    candidate = extracted_birth_date.strip().replace("/", "-").replace(".", "-")
    parts = candidate.split("-")
    if len(parts) != 3:
        return 0.0
    try:
        if len(parts[0]) == 4:
            parsed = date(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            parsed = date(int(parts[2]), int(parts[1]), int(parts[0]))
    except Exception:
        return 0.0
    return 100.0 if parsed == profile_birth_date else 0.0


def run_verification_ai_check(*, submission, profile) -> None:
    submission.ai_checked_at = timezone.now()
    model = (getattr(settings, "OPENROUTER_OCR_MODEL", "") or "").strip()
    api_key = (getattr(settings, "OPENROUTER_API_KEY", "") or "").strip()
    if not (model and api_key and submission.id_front_image):
        submission.ai_result_summary = "AI-Pruefung nicht verfuegbar."
        submission.save(update_fields=["ai_checked_at", "ai_result_summary", "updated_at"])
        return

    try:
        image_entries = [
            {"type": "image_url", "image_url": {"url": _file_to_data_url(submission.id_front_image)}},
        ]
        if submission.id_back_image:
            image_entries.append(
                {"type": "image_url", "image_url": {"url": _file_to_data_url(submission.id_back_image)}}
            )
        payload = {
            "model": model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Du bist ein OCR/ID-Checker. Extrahiere Name, Geburtsdatum, Dokumenttyp und gib JSON zurueck."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Bitte gib nur JSON mit Feldern: extracted_full_name, extracted_birth_date, "
                                "document_type, is_id_document, document_confidence (0-100), notes."
                            ),
                        },
                        *image_entries,
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
        }
        req = Request(
            url=f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                "X-Title": settings.OPENROUTER_APP_NAME,
            },
            method="POST",
        )
        with urlopen(req, timeout=45) as response:
            raw = json.loads(response.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"]
        parsed = json.loads(content) if isinstance(content, str) else content

        extracted_name = str(parsed.get("extracted_full_name", "") or "")
        extracted_birth_date = str(parsed.get("extracted_birth_date", "") or "")
        name_score = _name_similarity(extracted_name, profile.user.full_name)
        birth_date_score = _birth_date_similarity(extracted_birth_date, profile.birth_date)
        doc_confidence = _safe_float(parsed.get("document_confidence"), default=0.0)
        is_id_document = bool(parsed.get("is_id_document"))
        confidence_passed = is_id_document and doc_confidence >= 80 and name_score >= 80 and birth_date_score >= 80

        submission.ai_name_match_score = name_score
        submission.ai_birth_date_match_score = birth_date_score
        submission.ai_document_type_confidence = doc_confidence
        submission.ai_is_likely_id_document = is_id_document
        submission.ai_result_payload = {
            "model": model,
            "parsed": parsed,
            "threshold": 80,
            "confidence_passed": confidence_passed,
        }
        submission.ai_result_summary = (
            "Automatische Pruefung erfolgreich."
            if confidence_passed
            else "Automatische Pruefung mit Abweichungen. Manuelle Kontrolle erforderlich."
        )
        submission.save(
            update_fields=[
                "ai_checked_at",
                "ai_name_match_score",
                "ai_birth_date_match_score",
                "ai_document_type_confidence",
                "ai_is_likely_id_document",
                "ai_result_payload",
                "ai_result_summary",
                "updated_at",
            ]
        )
    except Exception as exc:
        submission.ai_result_summary = f"AI-Pruefung fehlgeschlagen: {exc}"
        submission.save(update_fields=["ai_checked_at", "ai_result_summary", "updated_at"])
