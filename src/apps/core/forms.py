from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import ClubConfiguration, PublicDocument, SocialClub, SocialClubOpeningHour, SocialClubReview


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


class SocialClubRegistrationForm(forms.ModelForm):
    class Meta:
        model = SocialClub
        fields = ["name", "email", "street_address", "postal_code", "city", "federal_state", "max_verified_members", "phone", "website", "public_description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + " form-input").strip()


class SocialClubSettingsForm(forms.ModelForm):
    class Meta:
        model = SocialClub
        fields = [
            "name",
            "public_description",
            "profile_image",
            "banner_image",
            "gallery_image_1",
            "gallery_image_2",
            "gallery_image_3",
            "gallery_image_4",
            "gallery_image_5",
            "email",
            "support_email",
            "membership_email",
            "prevention_email",
            "finance_email",
            "privacy_contact",
            "data_protection_officer",
            "phone",
            "website",
            "street_address",
            "postal_code",
            "city",
            "federal_state",
            "max_verified_members",
            "admission_fee",
            "monthly_membership_fee",
            "club_iban",
            "club_bic",
            "stripe_account_id",
            "stripe_dashboard_url",
            "board_representatives",
            "register_entry",
            "register_court",
            "tax_number",
            "vat_id",
            "supervisory_authority",
            "content_responsible",
            "responsible_person",
            "language_notice",
            "legal_basis_notice",
            "retention_notice",
            "external_services_text",
            "prevention_officer_name",
            "prevention_notice",
            "instagram_url",
            "telegram_url",
            "whatsapp_url",
        ]
        widgets = {
            "public_description": forms.Textarea(attrs={"rows": 5}),
            "board_representatives": forms.Textarea(attrs={"rows": 3}),
            "responsible_person": forms.Textarea(attrs={"rows": 3}),
            "language_notice": forms.Textarea(attrs={"rows": 3}),
            "legal_basis_notice": forms.Textarea(attrs={"rows": 3}),
            "retention_notice": forms.Textarea(attrs={"rows": 3}),
            "external_services_text": forms.Textarea(attrs={"rows": 3}),
            "prevention_notice": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            suffix = " form-input form-select" if isinstance(field.widget, forms.Select) else " form-input"
            field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + suffix).strip()


class SocialClubAdminRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    birth_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + " form-input").strip()

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def clean_email(self):
        from apps.accounts.models import User

        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Diese E-Mail-Adresse ist bereits vergeben.")
        return email


class SocialClubOpeningHourForm(forms.ModelForm):
    class Meta:
        model = SocialClubOpeningHour
        fields = ["weekday", "starts_at", "ends_at"]
        widgets = {
            "starts_at": forms.TimeInput(attrs={"type": "time"}),
            "ends_at": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            suffix = " form-input form-select" if isinstance(field.widget, forms.Select) else " form-input"
            field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + suffix).strip()

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get("starts_at")
        ends_at = cleaned_data.get("ends_at")
        if starts_at and ends_at and starts_at >= ends_at:
            raise forms.ValidationError("Die Endzeit muss spaeter als die Startzeit sein.")
        return cleaned_data


class SocialClubReviewForm(forms.ModelForm):
    class Meta:
        model = SocialClubReview
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} Sterne") for i in range(5, 0, -1)]),
            "comment": forms.Textarea(attrs={"rows": 4, "maxlength": 500}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rating"].label = "Sternebewertung"
        self.fields["comment"].label = "Kurztext"
        self.fields["comment"].required = False
        for field in self.fields.values():
            suffix = " form-input form-select" if isinstance(field.widget, forms.Select) else " form-input"
            field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + suffix).strip()

    def clean_comment(self):
        return (self.cleaned_data.get("comment") or "").strip()
