from __future__ import annotations

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

from .models import ClubConfiguration


def _normalized_services(value: str) -> list[str]:
    raw = value.replace("\r", "\n")
    parts = []
    for line in raw.split("\n"):
        for item in line.split(","):
            cleaned = item.strip()
            if cleaned:
                parts.append(cleaned)
    return parts


def _build_default_signature(values: dict[str, object]) -> tuple[str, str]:
    text_lines = [
        values["club_name"],
        values["club_slogan"],
        values["club_contact_address"],
        f"Telefon: {values['club_contact_phone']}" if values["club_contact_phone"] else "",
        f"E-Mail: {values['club_contact_email']}" if values["club_contact_email"] else "",
        f"Telegram: {values['telegram_url']}" if values["telegram_url"] else "",
        f"WhatsApp: {values['whatsapp_url']}" if values["whatsapp_url"] else "",
        f"Instagram: {values['instagram_url']}" if values["instagram_url"] else "",
        values["club_register_entry"],
        f"Steuernummer: {values['club_tax_number']}" if values["club_tax_number"] else "",
        values["club_language_notice"],
    ]
    text_signature = "\n".join(line.strip() for line in text_lines if line and str(line).strip())
    html_signature = "<br>".join(line for line in text_signature.splitlines() if line.strip())
    return text_signature, html_signature


def get_club_settings() -> dict[str, object]:
    try:
        config = ClubConfiguration.objects.first()
    except (OperationalError, ProgrammingError):
        config = None

    def pick(field_name: str, setting_name: str):
        value = getattr(config, field_name, "") if config else ""
        return value or getattr(settings, setting_name, "")

    external_services_text = getattr(config, "club_external_services_text", "") if config else ""
    external_services = _normalized_services(external_services_text) if external_services_text else list(
        getattr(settings, "CLUB_EXTERNAL_SERVICES", [])
    )

    values = {
        "app_name": pick("app_name", "APP_NAME"),
        "app_tagline": pick("app_tagline", "APP_TAGLINE"),
        "app_description": pick("app_description", "APP_DESCRIPTION"),
        "club_name": pick("club_name", "CLUB_NAME"),
        "club_slogan": getattr(config, "club_slogan", "") if config else "",
        "club_contact_email": pick("club_contact_email", "CLUB_CONTACT_EMAIL"),
        "club_support_email": pick("club_support_email", "CLUB_SUPPORT_EMAIL"),
        "club_contact_phone": pick("club_contact_phone", "CLUB_CONTACT_PHONE"),
        "telegram_url": pick("telegram_url", "CLUB_TELEGRAM_URL"),
        "whatsapp_url": pick("whatsapp_url", "CLUB_WHATSAPP_URL"),
        "club_contact_address": pick("club_contact_address", "CLUB_CONTACT_ADDRESS"),
        "club_board_representatives": pick("club_board_representatives", "CLUB_BOARD_REPRESENTATIVES"),
        "club_register_entry": pick("club_register_entry", "CLUB_REGISTER_ENTRY"),
        "club_register_court": pick("club_register_court", "CLUB_REGISTER_COURT"),
        "club_tax_number": pick("club_tax_number", "CLUB_TAX_NUMBER"),
        "club_vat_id": pick("club_vat_id", "CLUB_VAT_ID"),
        "club_supervisory_authority": pick("club_supervisory_authority", "CLUB_SUPERVISORY_AUTHORITY"),
        "club_content_responsible": pick("club_content_responsible", "CLUB_CONTENT_RESPONSIBLE"),
        "club_responsible_person": pick("club_responsible_person", "CLUB_RESPONSIBLE_PERSON"),
        "club_membership_email": pick("club_membership_email", "CLUB_MEMBERSHIP_EMAIL"),
        "club_prevention_email": pick("club_prevention_email", "CLUB_PREVENTION_EMAIL"),
        "club_finance_email": pick("club_finance_email", "CLUB_FINANCE_EMAIL"),
        "club_privacy_contact": pick("club_privacy_contact", "CLUB_PRIVACY_CONTACT"),
        "club_data_protection_officer": pick("club_data_protection_officer", "CLUB_DATA_PROTECTION_OFFICER"),
        "club_language_notice": pick("club_language_notice", "CLUB_LANGUAGE_NOTICE"),
        "club_legal_basis_notice": pick("club_legal_basis_notice", "CLUB_LEGAL_BASIS_NOTICE"),
        "club_retention_notice": pick("club_retention_notice", "CLUB_RETENTION_NOTICE"),
        "club_external_services": external_services,
        "prevention_officer_name": getattr(config, "prevention_officer_name", "") if config else "",
        "prevention_notice": getattr(config, "prevention_notice", "") if config else "",
        "instagram_url": getattr(config, "instagram_url", "") if config else "",
    }
    default_text, default_html = _build_default_signature(values)
    values["club_email_signature_text"] = getattr(config, "email_signature_text", "") if config and config.email_signature_text else default_text
    values["club_email_signature_html"] = getattr(config, "email_signature_html", "") if config and config.email_signature_html else default_html
    return values
