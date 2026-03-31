from __future__ import annotations

import io

from django.utils import timezone


def _build_pdf(title: str, lines: list[tuple[str, str]]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=A4)
    width, height = A4

    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(20 * mm, height - 25 * mm, title)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, height - 33 * mm, "Cannabis Social Club Leipzig Sued e.V.")
    pdf.drawString(20 * mm, height - 39 * mm, f"Erstellt am {timezone.localtime().strftime('%d.%m.%Y %H:%M')}")

    y = height - 55 * mm
    for label, value in lines:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(20 * mm, y, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(68 * mm, y, value or "-")
        y -= 7 * mm
        if y < 30 * mm:
            pdf.showPage()
            y = height - 25 * mm

    pdf.showPage()
    pdf.save()
    return stream.getvalue()


def membership_document_attachments(profile) -> list[tuple[str, bytes, str]]:
    user = profile.user
    mandate = profile.sepa_mandate
    common = [
        ("Name", user.full_name or user.email),
        ("E-Mail", user.email),
        ("Geburtsdatum", profile.birth_date.strftime("%d.%m.%Y")),
        ("Aufnahmedatum", profile.desired_join_date.strftime("%d.%m.%Y") if profile.desired_join_date else "-"),
        ("Adresse", profile.street_address),
        ("PLZ / Stadt", f"{profile.postal_code} {profile.city}".strip()),
        ("Telefon", profile.phone),
    ]

    application = _build_pdf(
        "Aufnahmeantrag",
        common
        + [
            ("Datenschutz akzeptiert", "Ja" if profile.privacy_accepted else "Nein"),
            ("Wichtige Vereinsinfos", "Ja" if profile.important_newsletter_opt_in else "Nein"),
            ("Optionaler Newsletter", "Ja" if profile.optional_newsletter_opt_in else "Nein"),
            ("Hinweise", profile.application_notes or "-"),
        ],
    )
    sepa = _build_pdf(
        "SEPA-Lastschriftmandat",
        common
        + [
            ("Kontoinhaber", profile.account_holder_name),
            ("Kreditinstitut", profile.bank_name),
            ("IBAN", mandate.iban if mandate else "-"),
            ("BIC", mandate.bic if mandate else "-"),
            ("Lastschrift akzeptiert", "Ja" if profile.direct_debit_accepted else "Nein"),
        ],
    )
    self_disclosure = _build_pdf(
        "Selbstauskunft",
        common
        + [
            ("Kein anderer CSC", "Ja" if profile.no_other_csc_membership else "Nein"),
            ("Wohnsitz Deutschland", "Ja" if profile.german_residence_confirmed else "Nein"),
            ("Mindestalter bestaetigt", "Ja" if profile.minimum_age_confirmed else "Nein"),
            ("Ausweisdaten aktuell", "Ja" if profile.id_document_confirmed else "Nein"),
        ],
    )
    member_card = _build_pdf(
        "Mitgliederausweis",
        [
            ("Mitglied", user.full_name or user.email),
            ("E-Mail", user.email),
            ("Mitgliedsnummer", str(profile.member_number or "wird nach Freigabe vergeben")),
            ("Status", profile.get_status_display()),
            ("Fruehester Eintritt", profile.desired_join_date.strftime("%d.%m.%Y") if profile.desired_join_date else "-"),
        ],
    )

    return [
        ("Aufnahmeantrag.pdf", application, "application/pdf"),
        ("SEPA-Lastschriftmandat.pdf", sepa, "application/pdf"),
        ("Selbstauskunft.pdf", self_disclosure, "application/pdf"),
        ("Mitgliederausweis.pdf", member_card, "application/pdf"),
    ]
