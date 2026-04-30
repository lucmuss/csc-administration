from __future__ import annotations

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

from .models import ClubConfiguration, SocialClub

ACTIVE_SOCIAL_CLUB_SESSION_KEY = "active_social_club_id"
ACTIVE_SOCIAL_CLUB_COOKIE = "active_social_club_id"
ACTIVE_FEDERAL_STATE_SESSION_KEY = "active_federal_state"
ACTIVE_FEDERAL_STATE_COOKIE = "active_federal_state"


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


def resolve_active_social_club(request=None):
    if request is None:
        return None
    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False) and not getattr(user, "is_superuser", False) and getattr(user, "social_club_id", None):
        return user.social_club
    club_id = request.session.get(ACTIVE_SOCIAL_CLUB_SESSION_KEY) or request.COOKIES.get(ACTIVE_SOCIAL_CLUB_COOKIE)
    if not club_id:
        return SocialClub.objects.filter(is_active=True, is_approved=True).order_by("name").first()
    return SocialClub.objects.filter(id=club_id, is_active=True, is_approved=True).first() or SocialClub.objects.filter(is_active=True, is_approved=True).order_by("name").first()


def resolve_active_federal_state(request=None) -> str:
    if request is None:
        return ""
    state = (request.session.get(ACTIVE_FEDERAL_STATE_SESSION_KEY) or request.COOKIES.get(ACTIVE_FEDERAL_STATE_COOKIE) or "").strip()
    valid_codes = {code for code, _label in SocialClub.FEDERAL_STATE_CHOICES}
    return state if state in valid_codes else ""


def get_club_settings(*, social_club: SocialClub | None = None) -> dict[str, object]:
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

    if social_club:
        club_address = f"{social_club.street_address}, {social_club.postal_code} {social_club.city}".strip(", " )
        values.update(
            {
                "club_name": social_club.name or values["club_name"],
                "club_contact_email": social_club.email or values["club_contact_email"],
                "club_support_email": social_club.support_email or values["club_support_email"],
                "club_membership_email": social_club.membership_email or values["club_membership_email"],
                "club_prevention_email": social_club.prevention_email or values["club_prevention_email"],
                "club_finance_email": social_club.finance_email or values["club_finance_email"],
                "club_privacy_contact": social_club.privacy_contact or values["club_privacy_contact"],
                "club_data_protection_officer": social_club.data_protection_officer or values["club_data_protection_officer"],
                "club_contact_phone": social_club.phone or values["club_contact_phone"],
                "club_contact_address": club_address or values["club_contact_address"],
                "club_board_representatives": social_club.board_representatives or values["club_board_representatives"],
                "club_register_entry": social_club.register_entry or values["club_register_entry"],
                "club_register_court": social_club.register_court or values["club_register_court"],
                "club_tax_number": social_club.tax_number or values["club_tax_number"],
                "club_vat_id": social_club.vat_id or values["club_vat_id"],
                "club_supervisory_authority": social_club.supervisory_authority or values["club_supervisory_authority"],
                "club_content_responsible": social_club.content_responsible or values["club_content_responsible"],
                "club_responsible_person": social_club.responsible_person or values["club_responsible_person"],
                "club_language_notice": social_club.language_notice or values["club_language_notice"],
                "club_legal_basis_notice": social_club.legal_basis_notice or values["club_legal_basis_notice"],
                "club_retention_notice": social_club.retention_notice or values["club_retention_notice"],
                "prevention_officer_name": social_club.prevention_officer_name or values["prevention_officer_name"],
                "prevention_notice": social_club.prevention_notice or values["prevention_notice"],
                "instagram_url": social_club.instagram_url or values["instagram_url"],
                "telegram_url": social_club.telegram_url or values["telegram_url"],
                "whatsapp_url": social_club.whatsapp_url or values["whatsapp_url"],
                "club_external_services": _normalized_services(social_club.external_services_text)
                if social_club.external_services_text
                else values["club_external_services"],
            }
        )

    return values
