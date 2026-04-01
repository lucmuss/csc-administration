from __future__ import annotations

from django.utils import timezone

from .club import get_club_settings


def club_letterhead_lines() -> list[str]:
    club_settings = get_club_settings()
    lines = [str(club_settings["club_name"]).strip()]
    slogan = str(club_settings.get("club_slogan", "") or "").strip()
    if slogan:
        lines.append(slogan)
    lines.extend(
        line.strip()
        for line in str(club_settings.get("club_contact_address", "") or "").splitlines()
        if line.strip()
    )
    if club_settings.get("club_contact_phone"):
        lines.append(f"Telefon: {club_settings['club_contact_phone']}")
    if club_settings.get("club_contact_email"):
        lines.append(f"E-Mail: {club_settings['club_contact_email']}")
    support_email = str(club_settings.get("club_support_email", "") or "").strip()
    if support_email and support_email != str(club_settings.get("club_contact_email", "") or "").strip():
        lines.append(f"Support: {support_email}")
    return lines


def club_footer_lines() -> list[str]:
    club_settings = get_club_settings()
    lines = club_letterhead_lines()
    for extra in (
        club_settings.get("club_register_entry"),
        club_settings.get("club_register_court"),
        club_settings.get("club_tax_number") and f"Steuernummer: {club_settings['club_tax_number']}",
        club_settings.get("club_vat_id") and f"USt-ID: {club_settings['club_vat_id']}",
        club_settings.get("club_supervisory_authority"),
        club_settings.get("club_content_responsible") or club_settings.get("club_responsible_person"),
        club_settings.get("club_language_notice"),
    ):
        if extra:
            lines.append(str(extra).strip())
    return [line for line in lines if line]


def finance_footer_lines() -> list[str]:
    club_settings = get_club_settings()
    lines = club_footer_lines()
    finance_email = str(club_settings.get("club_finance_email", "") or "").strip()
    membership_email = str(club_settings.get("club_membership_email", "") or "").strip()
    if finance_email:
        lines.append(f"Finanzen: {finance_email}")
    if membership_email:
        lines.append(f"Mitgliedschaft: {membership_email}")
    return lines


def membership_footer_lines() -> list[str]:
    club_settings = get_club_settings()
    lines = club_footer_lines()
    membership_email = str(club_settings.get("club_membership_email", "") or "").strip()
    prevention_email = str(club_settings.get("club_prevention_email", "") or "").strip()
    prevention_officer = str(club_settings.get("prevention_officer_name", "") or "").strip()
    if membership_email:
        lines.append(f"Mitgliedschaft: {membership_email}")
    if prevention_email:
        lines.append(f"Praevention: {prevention_email}")
    if prevention_officer:
        lines.append(f"Praeventionsbeauftragte:r: {prevention_officer}")
    return lines


def governance_footer_lines() -> list[str]:
    club_settings = get_club_settings()
    lines = club_footer_lines()
    responsible = str(club_settings.get("club_content_responsible", "") or club_settings.get("club_responsible_person", "") or "").strip()
    support_email = str(club_settings.get("club_support_email", "") or "").strip()
    if responsible:
        lines.append(f"Verantwortlich: {responsible}")
    if support_email:
        lines.append(f"Support: {support_email}")
    return lines


def draw_club_letterhead(pdf, *, width, height, title: str, right_lines: list[str] | None = None):
    from reportlab.lib.units import mm

    top_y = height - 20 * mm
    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(20 * mm, top_y, title)
    pdf.setFont("Helvetica", 9)
    left_lines = club_letterhead_lines()
    for index, line in enumerate(left_lines[:7], start=1):
        pdf.drawString(20 * mm, top_y - (index * 5 * mm), line)
    if right_lines:
        current_y = top_y
        for index, line in enumerate(right_lines):
            if index == 0:
                pdf.setFont("Helvetica-Bold", 11)
            else:
                pdf.setFont("Helvetica", 9)
            pdf.drawRightString(width - 20 * mm, current_y, str(line))
            current_y -= 6 * mm
    return top_y - max(len(left_lines[:7]) * 5 * mm, (len(right_lines or []) - 1) * 6 * mm if right_lines else 0)


def draw_club_footer(pdf, *, width, footer_y, lines: list[str] | None = None):
    from reportlab.lib.units import mm

    pdf.line(20 * mm, footer_y + 8 * mm, width - 20 * mm, footer_y + 8 * mm)
    footer_text = pdf.beginText(20 * mm, footer_y)
    footer_text.setFont("Helvetica", 8)
    for line in lines or club_footer_lines():
        footer_text.textLine(line)
    pdf.drawText(footer_text)


def generated_at_label() -> str:
    return timezone.localtime().strftime("%d.%m.%Y %H:%M")
