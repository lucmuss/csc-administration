from django import forms

from .models import ClubConfiguration, PublicDocument


class PublicDocumentForm(forms.ModelForm):
    class Meta:
        model = PublicDocument
        fields = ["title", "category", "description", "file", "is_public", "display_order"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-checkbox"
            else:
                suffix = " form-input form-select" if isinstance(field.widget, forms.Select) else " form-input"
                field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + suffix).strip()


class ClubConfigurationForm(forms.ModelForm):
    class Meta:
        model = ClubConfiguration
        fields = [
            "app_name",
            "app_tagline",
            "app_description",
            "club_name",
            "club_slogan",
            "club_contact_email",
            "club_support_email",
            "club_contact_phone",
            "telegram_url",
            "whatsapp_url",
            "club_contact_address",
            "club_board_representatives",
            "club_register_entry",
            "club_register_court",
            "club_tax_number",
            "club_vat_id",
            "club_supervisory_authority",
            "club_content_responsible",
            "club_responsible_person",
            "club_membership_email",
            "club_prevention_email",
            "club_finance_email",
            "club_privacy_contact",
            "club_data_protection_officer",
            "club_language_notice",
            "club_legal_basis_notice",
            "club_retention_notice",
            "club_external_services_text",
            "prevention_officer_name",
            "prevention_notice",
            "instagram_url",
            "email_signature_text",
            "email_signature_html",
        ]
        widgets = {
            "app_description": forms.Textarea(attrs={"rows": 3}),
            "club_contact_address": forms.Textarea(attrs={"rows": 4}),
            "club_board_representatives": forms.Textarea(attrs={"rows": 3}),
            "club_responsible_person": forms.Textarea(attrs={"rows": 4}),
            "club_language_notice": forms.Textarea(attrs={"rows": 3}),
            "club_legal_basis_notice": forms.Textarea(attrs={"rows": 3}),
            "club_retention_notice": forms.Textarea(attrs={"rows": 3}),
            "club_external_services_text": forms.Textarea(attrs={"rows": 4}),
            "prevention_notice": forms.Textarea(attrs={"rows": 4}),
            "email_signature_text": forms.Textarea(attrs={"rows": 6}),
            "email_signature_html": forms.Textarea(attrs={"rows": 6}),
        }
        help_texts = {
            "club_external_services_text": "Ein Dienst pro Zeile oder komma-separiert, z. B. Stripe, OpenRouter.",
            "email_signature_text": "Optional. Wenn leer, wird automatisch eine Signatur aus den Clubdaten erzeugt.",
            "email_signature_html": "Optional. Wenn leer, wird automatisch eine HTML-Signatur aus den Clubdaten erzeugt.",
        }
        labels = {
            "app_name": "App-Name",
            "app_tagline": "App-Tagline",
            "app_description": "App-Beschreibung",
            "club_name": "Vereinsname",
            "club_slogan": "Slogan / Untertitel",
            "club_contact_email": "Allgemeine Kontakt-E-Mail",
            "club_support_email": "Support-E-Mail",
            "club_contact_phone": "Telefon",
            "telegram_url": "Telegram-Link",
            "whatsapp_url": "WhatsApp-Link",
            "club_contact_address": "Anschrift",
            "club_board_representatives": "Vertretungsberechtigte",
            "club_register_entry": "Vereinsregistereintrag",
            "club_register_court": "Registergericht",
            "club_tax_number": "Steuernummer",
            "club_vat_id": "USt-ID / Wirtschafts-ID",
            "club_supervisory_authority": "Aufsichtsbehoerde",
            "club_content_responsible": "Inhaltlich verantwortlich",
            "club_responsible_person": "Verantwortlich gemaess § 55 Abs. 2 RStV",
            "club_membership_email": "Kontakt Mitgliedschaft",
            "club_prevention_email": "Kontakt Praevention",
            "club_finance_email": "Kontakt Finanzen",
            "club_privacy_contact": "Datenschutzkontakt",
            "club_data_protection_officer": "Datenschutzbeauftragte Stelle",
            "club_language_notice": "Sprachhinweis",
            "club_legal_basis_notice": "Hinweis zu Rechtsgrundlagen",
            "club_retention_notice": "Hinweis zu Aufbewahrung",
            "club_external_services_text": "Externe Dienstleister",
            "prevention_officer_name": "Praeventionsbeauftragte:r",
            "prevention_notice": "Praeventionshinweis",
            "instagram_url": "Instagram-URL",
            "email_signature_text": "E-Mail-Signatur Text",
            "email_signature_html": "E-Mail-Signatur HTML",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            suffix = " form-input"
            if isinstance(field.widget, forms.Select):
                suffix = " form-input form-select"
            field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + suffix).strip()
