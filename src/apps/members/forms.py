from datetime import date, timedelta
import re

from django import forms
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone

from apps.accounts.models import User
from apps.core.club import ACTIVE_SOCIAL_CLUB_COOKIE, ACTIVE_SOCIAL_CLUB_SESSION_KEY, resolve_active_social_club
from apps.core.models import SocialClub
from apps.finance.models import SepaMandate
from apps.messaging.services import sync_member_messaging_preferences
from apps.participation.models import MemberEngagement

from .models import Profile, VerificationSubmission


NAME_RE = re.compile(r"^[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß' -]{2,149}$")
POSTAL_CODE_RE = re.compile(r"^\d{5}$")
BIC_RE = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")
IBAN_RE = re.compile(r"^[A-Z]{2}[0-9A-Z]{13,32}$")


def _validate_person_name(value: str, label: str) -> str:
    cleaned = " ".join(value.split()).strip()
    if len(cleaned) < 3:
        raise forms.ValidationError(f"{label} muss mindestens 3 Zeichen enthalten.")
    if any(char.isdigit() for char in cleaned):
        raise forms.ValidationError(f"{label} darf keine Zahlen enthalten.")
    if not NAME_RE.fullmatch(cleaned):
        raise forms.ValidationError(f"{label} enthaelt unzulaessige Zeichen.")
    return cleaned


def _validate_email_address(value: str) -> str:
    cleaned = value.strip().lower()
    validate_email(cleaned)
    domain = cleaned.rsplit("@", 1)[-1]
    if "." not in domain:
        raise forms.ValidationError("Bitte eine vollstaendige E-Mail-Adresse mit gueltiger Domain angeben.")
    return cleaned


def _validate_postal_code(value: str) -> str:
    cleaned = value.strip()
    if not POSTAL_CODE_RE.fullmatch(cleaned):
        raise forms.ValidationError("Bitte eine gueltige deutsche Postleitzahl mit 5 Ziffern eingeben.")
    return cleaned


def _validate_bic(value: str) -> str:
    cleaned = value.replace(" ", "").upper()
    if not BIC_RE.fullmatch(cleaned):
        raise forms.ValidationError("Bitte eine gueltige BIC eingeben.")
    return cleaned


def _iban_checksum_valid(iban: str) -> bool:
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(int(char, 36)) for char in rearranged)
    remainder = 0
    for offset in range(0, len(numeric), 7):
        remainder = int(f"{remainder}{numeric[offset:offset + 7]}") % 97
    return remainder == 1


def _validate_iban(value: str) -> str:
    cleaned = value.replace(" ", "").upper()
    if not IBAN_RE.fullmatch(cleaned):
        raise forms.ValidationError("Bitte eine gueltige IBAN eingeben.")
    if not _iban_checksum_valid(cleaned):
        raise forms.ValidationError("Die IBAN-Pruefsumme ist ungueltig.")
    return cleaned


def _validate_bank_name(value: str) -> str:
    cleaned = " ".join(value.split()).strip()
    if len(cleaned) < 2:
        raise forms.ValidationError("Bitte ein gueltiges Kreditinstitut angeben.")
    return cleaned


def _apply_form_control(widget: forms.Widget) -> None:
    existing_classes = widget.attrs.get("class", "").strip()
    if isinstance(widget, forms.CheckboxInput):
        control_class = "form-checkbox"
    elif isinstance(widget, forms.RadioSelect):
        control_class = "form-radio-group"
    elif isinstance(widget, forms.Textarea):
        control_class = "form-input form-textarea"
    elif isinstance(widget, forms.Select):
        control_class = "form-input form-select"
    else:
        control_class = "form-input"
    widget.attrs["class"] = " ".join(part for part in [existing_classes, control_class] if part)


def _default_join_date() -> date:
    today = timezone.localdate()
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


class MemberRegistrationForm(forms.Form):
    social_club = forms.ModelChoiceField(
        queryset=SocialClub.objects.filter(is_active=True, is_approved=True).order_by("name"),
        required=False,
        label="Social Club",
        empty_label="Social Club auswaehlen",
    )
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    password = forms.CharField(widget=forms.PasswordInput)

    def _resolve_minimum_age(self) -> int:
        default_age = int(getattr(settings, "MEMBER_MINIMUM_AGE", 21))
        selected_club = None
        if self.is_bound and "social_club" in self.fields:
            bound_club = str(self.data.get("social_club") or "").strip()
            if bound_club:
                selected_club = self.fields["social_club"].queryset.filter(pk=bound_club).first()
        elif self.request is not None:
            selected_club = resolve_active_social_club(self.request)
        if not selected_club and "social_club" in self.fields:
            initial_club = self.initial.get("social_club")
            if hasattr(initial_club, "minimum_age"):
                selected_club = initial_club
            elif initial_club:
                selected_club = self.fields["social_club"].queryset.filter(pk=initial_club).first()
        if selected_club and getattr(selected_club, "minimum_age", None):
            return int(selected_club.minimum_age)
        return default_age

    def __init__(self, *args, federal_state: str = "", request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        state_code = (federal_state or "").strip()
        if state_code:
            filtered = self.fields["social_club"].queryset.filter(federal_state=state_code)
            if filtered.exists():
                self.fields["social_club"].queryset = filtered
        if request is not None:
            saved_club_id = request.session.get(ACTIVE_SOCIAL_CLUB_SESSION_KEY) or request.COOKIES.get(ACTIVE_SOCIAL_CLUB_COOKIE)
            if saved_club_id:
                self.fields.pop("social_club", None)
        try:
            requires_club_choice = "social_club" in self.fields and self.fields["social_club"].queryset.exists()
        except (RuntimeError, OperationalError, ProgrammingError):
            requires_club_choice = False
        if "social_club" in self.fields:
            self.fields["social_club"].required = requires_club_choice
            if requires_club_choice:
                self.fields["social_club"].widget.attrs["required"] = True
        self.fields["email"].widget.attrs.update({"autocomplete": "email", "placeholder": "name@beispiel.de"})
        if "social_club" in self.fields:
            self.fields["social_club"].widget.attrs.setdefault("data-search-hint", "z. B. Leipzig")
        self.fields["first_name"].widget.attrs.setdefault("autocomplete", "given-name")
        self.fields["last_name"].widget.attrs.setdefault("autocomplete", "family-name")
        self.fields["birth_date"].widget.attrs.setdefault("autocomplete", "bday")
        minimum_age = self._resolve_minimum_age()
        self.fields["birth_date"].help_text = f"Mindestens {minimum_age} Jahre erforderlich."
        max_birth_date = timezone.localdate() - timedelta(days=minimum_age * 365)
        self.fields["birth_date"].widget.attrs.setdefault("min", "1920-01-01")
        self.fields["birth_date"].widget.attrs.setdefault("max", max_birth_date.isoformat())
        self.fields["password"].widget.attrs.update({"autocomplete": "new-password", "placeholder": "Passwort"})
        for field in self.fields.values():
            _apply_form_control(field.widget)

    def clean_email(self):
        email = _validate_email_address(self.cleaned_data["email"])
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("E-Mail ist bereits registriert")
        return email

    def clean_first_name(self):
        return _validate_person_name(self.cleaned_data["first_name"], "Vorname")

    def clean_last_name(self):
        return _validate_person_name(self.cleaned_data["last_name"], "Nachname")

    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        today = date.today()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        minimum_age = self._resolve_minimum_age()
        if age < minimum_age:
            raise forms.ValidationError(f"Mindestens {minimum_age} Jahre erforderlich")
        return birth_date

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self) -> User:
        bootstrap_board = not User.objects.exists()
        selected_club = self.cleaned_data.get("social_club")
        if not selected_club and self.request is not None:
            selected_club = resolve_active_social_club(self.request)
        if not selected_club:
            selected_club = SocialClub.objects.filter(is_active=True, is_approved=True).order_by("id").first()
        user = User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            role=User.ROLE_BOARD if bootstrap_board else User.ROLE_MEMBER,
            is_staff=bootstrap_board,
            is_superuser=bootstrap_board,
            social_club=selected_club,
        )
        profile = Profile.objects.create(
            user=user,
            birth_date=self.cleaned_data["birth_date"],
            status=Profile.STATUS_ACTIVE if bootstrap_board else Profile.STATUS_PENDING,
            is_verified=bootstrap_board,
            monthly_counter_key=date.today().strftime("%Y-%m"),
        )
        profile.full_clean()
        profile.save()
        if bootstrap_board:
            profile.allocate_member_number()
        MemberEngagement.objects.create(
            profile=profile,
            registration_deadline=timezone.localdate() + timedelta(days=14) if not bootstrap_board else None,
            registration_completed=bootstrap_board,
        )
        return user


class MemberOnboardingForm(forms.Form):
    desired_join_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Aufnahmedatum",
        help_text="Das frueheste Eintrittsdatum muss heute oder in der Zukunft liegen.",
    )
    street_address = forms.CharField(max_length=255, label="Strasse, Hausnummer")
    postal_code = forms.CharField(max_length=10, label="Postleitzahl")
    city = forms.CharField(max_length=120, label="Stadt")
    phone = forms.CharField(max_length=32, label="Telefonnummer")
    iban = forms.CharField(max_length=34, label="IBAN")
    bic = forms.CharField(max_length=11, label="BIC")
    bank_name = forms.CharField(max_length=150, label="Kreditinstitut")
    account_holder_name = forms.CharField(max_length=255, label="Kontoinhaber")
    privacy_accepted = forms.BooleanField(label="Datenschutzerklaerung gelesen")
    direct_debit_accepted = forms.BooleanField(label="Lastschriftmandat akzeptiert")
    no_other_csc_membership = forms.BooleanField(label="Kein Mitglied in anderer Anbaugemeinschaft")
    german_residence_confirmed = forms.BooleanField(label="Fester Wohnsitz in Deutschland")
    minimum_age_confirmed = forms.BooleanField(label="Mindestalter bestaetigt")
    id_document_confirmed = forms.BooleanField(label="Aktueller Lichtbildausweis bestaetigt")
    important_newsletter_opt_in = forms.BooleanField(label="Wichtige Vereinsankuendigungen erlauben")
    optional_newsletter_opt_in = forms.TypedChoiceField(
        label="Optionaler Newsletter",
        choices=((True, "Ja"), (False, "Nein")),
        coerce=lambda value: value in {True, "True", "true", "1"},
        widget=forms.RadioSelect,
    )
    application_notes = forms.CharField(
        label="Weitere Hinweise",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, profile: Profile, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)
        active_mandate = profile.sepa_mandate or SepaMandate.objects.filter(profile=profile, is_active=True).first()
        self.fields["desired_join_date"].initial = profile.desired_join_date or _default_join_date()
        self.fields["street_address"].initial = profile.street_address
        self.fields["postal_code"].initial = profile.postal_code
        self.fields["city"].initial = profile.city
        self.fields["phone"].initial = profile.phone
        self.fields["bank_name"].initial = profile.bank_name
        self.fields["account_holder_name"].initial = profile.account_holder_name or profile.user.full_name
        self.fields["privacy_accepted"].initial = profile.privacy_accepted
        self.fields["direct_debit_accepted"].initial = profile.direct_debit_accepted
        self.fields["no_other_csc_membership"].initial = profile.no_other_csc_membership
        self.fields["german_residence_confirmed"].initial = profile.german_residence_confirmed
        self.fields["minimum_age_confirmed"].initial = profile.minimum_age_confirmed
        self.fields["id_document_confirmed"].initial = profile.id_document_confirmed
        self.fields["important_newsletter_opt_in"].initial = profile.important_newsletter_opt_in
        self.fields["optional_newsletter_opt_in"].initial = profile.optional_newsletter_opt_in
        self.fields["application_notes"].initial = profile.application_notes
        if active_mandate:
            self.fields["iban"].initial = active_mandate.iban
            self.fields["bic"].initial = active_mandate.bic
        self.fields["phone"].widget.attrs.setdefault("autocomplete", "tel")
        self.fields["street_address"].widget.attrs.setdefault("autocomplete", "street-address")
        self.fields["postal_code"].widget.attrs.setdefault("autocomplete", "postal-code")
        self.fields["city"].widget.attrs.setdefault("autocomplete", "address-level2")
        self.fields["iban"].widget.attrs.setdefault("placeholder", "DE...")
        self.fields["bic"].widget.attrs.setdefault("placeholder", "BIC")
        self.fields["account_holder_name"].widget.attrs.setdefault("autocomplete", "name")
        minimum_age = getattr(settings, "MEMBER_MINIMUM_AGE", 21)
        self.fields["minimum_age_confirmed"].label = f"Ich habe das {minimum_age}. Lebensjahr vollendet."
        for field in self.fields.values():
            _apply_form_control(field.widget)

    def clean_desired_join_date(self):
        desired_join_date = self.cleaned_data["desired_join_date"]
        if desired_join_date < timezone.localdate():
            raise forms.ValidationError("Das Aufnahmedatum muss heute oder in der Zukunft liegen.")
        return desired_join_date

    def clean_postal_code(self):
        return _validate_postal_code(self.cleaned_data["postal_code"])

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip().replace(" ", "")
        allowed = set("+0123456789")
        if not phone or any(char not in allowed for char in phone):
            raise forms.ValidationError("Bitte nur Zahlen und optional ein Pluszeichen verwenden.")
        return phone

    def clean_iban(self):
        return _validate_iban(self.cleaned_data["iban"])

    def clean_bic(self):
        return _validate_bic(self.cleaned_data["bic"])

    def clean_bank_name(self):
        return _validate_bank_name(self.cleaned_data["bank_name"])

    def clean_account_holder_name(self):
        return _validate_person_name(self.cleaned_data["account_holder_name"], "Kontoinhaber")

    def save(self) -> Profile:
        self.profile.desired_join_date = self.cleaned_data["desired_join_date"]
        self.profile.street_address = self.cleaned_data["street_address"].strip()
        self.profile.postal_code = self.cleaned_data["postal_code"].strip()
        self.profile.city = self.cleaned_data["city"].strip()
        self.profile.phone = self.cleaned_data["phone"].strip()
        self.profile.bank_name = self.cleaned_data["bank_name"].strip()
        self.profile.account_holder_name = self.cleaned_data["account_holder_name"].strip()
        self.profile.privacy_accepted = self.cleaned_data["privacy_accepted"]
        self.profile.direct_debit_accepted = self.cleaned_data["direct_debit_accepted"]
        self.profile.no_other_csc_membership = self.cleaned_data["no_other_csc_membership"]
        self.profile.german_residence_confirmed = self.cleaned_data["german_residence_confirmed"]
        self.profile.minimum_age_confirmed = self.cleaned_data["minimum_age_confirmed"]
        self.profile.id_document_confirmed = self.cleaned_data["id_document_confirmed"]
        self.profile.important_newsletter_opt_in = self.cleaned_data["important_newsletter_opt_in"]
        self.profile.optional_newsletter_opt_in = self.cleaned_data["optional_newsletter_opt_in"]
        self.profile.application_notes = self.cleaned_data["application_notes"].strip()
        self.profile.mark_registration_completed()
        self.profile.save(
            update_fields=[
                "desired_join_date",
                "street_address",
                "postal_code",
                "city",
                "phone",
                "bank_name",
                "account_holder_name",
                "privacy_accepted",
                "direct_debit_accepted",
                "no_other_csc_membership",
                "german_residence_confirmed",
                "minimum_age_confirmed",
                "id_document_confirmed",
                "important_newsletter_opt_in",
                "optional_newsletter_opt_in",
                "application_notes",
                "registration_completed_at",
                "updated_at",
            ]
        )

        account_holder = self.profile.account_holder_name or self.profile.user.full_name or self.profile.user.email
        mandate = self.profile.sepa_mandate or SepaMandate.objects.filter(profile=self.profile, is_active=True).first()
        if mandate:
            mandate.iban = self.cleaned_data["iban"]
            mandate.bic = self.cleaned_data["bic"]
            mandate.account_holder = account_holder
            mandate.is_active = True
            mandate.save(update_fields=["iban", "bic", "account_holder", "is_active", "updated_at"])
        else:
            mandate = SepaMandate.objects.create(
                profile=self.profile,
                iban=self.cleaned_data["iban"],
                bic=self.cleaned_data["bic"],
                account_holder=account_holder,
                mandate_reference=f"CSC-ONBOARD-{self.profile.user_id}",
                is_active=True,
            )
        if self.profile.sepa_mandate_id != mandate.id:
            self.profile.sepa_mandate = mandate
            self.profile.save(update_fields=["sepa_mandate", "updated_at"])

        engagement, _ = MemberEngagement.objects.get_or_create(profile=self.profile)
        engagement.registration_completed = True
        engagement.registration_deadline = None
        engagement.save(update_fields=["registration_completed", "registration_deadline", "updated_at"])
        sync_member_messaging_preferences(self.profile)
        return self.profile


class MemberProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, label="Vorname")
    last_name = forms.CharField(max_length=150, label="Nachname")
    email = forms.EmailField(label="E-Mail")
    phone = forms.CharField(max_length=32, label="Telefonnummer")
    street_address = forms.CharField(max_length=255, label="Strasse, Hausnummer", required=False)
    postal_code = forms.CharField(max_length=10, label="Postleitzahl", required=False)
    city = forms.CharField(max_length=120, label="Stadt", required=False)
    bank_name = forms.CharField(max_length=150, label="Kreditinstitut")
    account_holder_name = forms.CharField(max_length=255, label="Kontoinhaber")
    iban = forms.CharField(max_length=34, label="IBAN")
    bic = forms.CharField(max_length=11, label="BIC")
    optional_newsletter_opt_in = forms.TypedChoiceField(
        label="Preislisten und Angebote",
        choices=((True, "Ja"), (False, "Nein")),
        coerce=lambda value: value in {True, "True", "true", "1"},
        widget=forms.RadioSelect,
    )
    preferred_language = forms.ChoiceField(
        label="Benutzeroberflaeche",
        choices=Profile.LANGUAGE_CHOICES,
        initial=Profile.LANGUAGE_DE,
    )
    payment_method_preference = forms.ChoiceField(
        label="Beitrags-Zahlungsart",
        choices=Profile.PAYMENT_METHOD_CHOICES,
        initial=Profile.PAYMENT_METHOD_SEPA,
        required=False,
    )
    application_notes = forms.CharField(label="Weitere Hinweise", required=False, widget=forms.Textarea(attrs={"rows": 4}))

    def __init__(self, *args, profile: Profile, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)
        mandate = profile.sepa_mandate or SepaMandate.objects.filter(profile=profile, is_active=True).first()
        self.fields["first_name"].initial = profile.user.first_name
        self.fields["last_name"].initial = profile.user.last_name
        self.fields["email"].initial = profile.user.email
        self.fields["phone"].initial = profile.phone
        self.fields["street_address"].initial = profile.street_address
        self.fields["postal_code"].initial = profile.postal_code
        self.fields["city"].initial = profile.city
        self.fields["bank_name"].initial = profile.bank_name
        self.fields["account_holder_name"].initial = profile.account_holder_name or profile.user.full_name
        self.fields["optional_newsletter_opt_in"].initial = profile.optional_newsletter_opt_in
        self.fields["preferred_language"].initial = profile.preferred_language or Profile.LANGUAGE_DE
        self.fields["payment_method_preference"].initial = profile.payment_method_preference or Profile.PAYMENT_METHOD_SEPA
        self.fields["application_notes"].initial = profile.application_notes
        if mandate:
            self.fields["iban"].initial = mandate.iban
            self.fields["bic"].initial = mandate.bic
        self.fields["email"].widget.attrs.update({"autocomplete": "email", "inputmode": "email"})
        self.fields["phone"].widget.attrs.setdefault("autocomplete", "tel")
        self.fields["street_address"].widget.attrs.setdefault("autocomplete", "street-address")
        self.fields["postal_code"].widget.attrs.setdefault("autocomplete", "postal-code")
        self.fields["city"].widget.attrs.setdefault("autocomplete", "address-level2")
        for field in self.fields.values():
            _apply_form_control(field.widget)

    def clean_email(self):
        email = _validate_email_address(self.cleaned_data["email"])
        if User.objects.exclude(pk=self.profile.user_id).filter(email=email).exists():
            raise forms.ValidationError("Diese E-Mail-Adresse wird bereits verwendet.")
        return email

    def clean_first_name(self):
        return _validate_person_name(self.cleaned_data["first_name"], "Vorname")

    def clean_last_name(self):
        return _validate_person_name(self.cleaned_data["last_name"], "Nachname")

    def clean_postal_code(self):
        postal_code = self.cleaned_data["postal_code"].strip()
        if not postal_code:
            return postal_code
        return _validate_postal_code(postal_code)

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip().replace(" ", "")
        allowed = set("+0123456789")
        if not phone or any(char not in allowed for char in phone):
            raise forms.ValidationError("Bitte nur Zahlen und optional ein Pluszeichen verwenden.")
        return phone

    def clean_iban(self):
        return _validate_iban(self.cleaned_data["iban"])

    def clean_bic(self):
        return _validate_bic(self.cleaned_data["bic"])

    def clean_bank_name(self):
        return _validate_bank_name(self.cleaned_data["bank_name"])

    def clean_account_holder_name(self):
        return _validate_person_name(self.cleaned_data["account_holder_name"], "Kontoinhaber")

    def save(self) -> Profile:
        user = self.profile.user
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"]
        user.save(update_fields=["first_name", "last_name", "email"])

        self.profile.phone = self.cleaned_data["phone"].strip()
        self.profile.street_address = self.cleaned_data["street_address"].strip()
        self.profile.postal_code = self.cleaned_data["postal_code"].strip()
        self.profile.city = self.cleaned_data["city"].strip()
        self.profile.bank_name = self.cleaned_data["bank_name"].strip()
        self.profile.account_holder_name = self.cleaned_data["account_holder_name"].strip()
        self.profile.optional_newsletter_opt_in = self.cleaned_data["optional_newsletter_opt_in"]
        self.profile.preferred_language = self.cleaned_data["preferred_language"]
        self.profile.payment_method_preference = self.cleaned_data.get("payment_method_preference") or self.profile.payment_method_preference
        self.profile.application_notes = self.cleaned_data["application_notes"].strip()
        self.profile.save(
            update_fields=[
                "phone",
                "street_address",
                "postal_code",
                "city",
                "bank_name",
                "account_holder_name",
                "optional_newsletter_opt_in",
                "preferred_language",
                "payment_method_preference",
                "application_notes",
                "updated_at",
            ]
        )

        mandate = self.profile.sepa_mandate or SepaMandate.objects.filter(profile=self.profile, is_active=True).first()
        iban = self.cleaned_data["iban"]
        bic = self.cleaned_data["bic"]
        if mandate:
            mandate.iban = iban
            mandate.bic = bic
            mandate.account_holder = self.profile.account_holder_name or user.full_name or user.email
            mandate.is_active = True
            mandate.save(update_fields=["iban", "bic", "account_holder", "is_active", "updated_at"])
        else:
            mandate = SepaMandate.objects.create(
                profile=self.profile,
                iban=iban,
                bic=bic,
                account_holder=self.profile.account_holder_name or user.full_name or user.email,
                mandate_reference=f"CSC-PROFILE-{self.profile.user_id}",
                is_active=True,
            )
        if self.profile.sepa_mandate_id != mandate.id:
            self.profile.sepa_mandate = mandate
            self.profile.save(update_fields=["sepa_mandate", "updated_at"])

        sync_member_messaging_preferences(self.profile)
        return self.profile


class VerificationSubmissionForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024

    class Meta:
        model = VerificationSubmission
        fields = [
            "id_front_image",
            "id_back_image",
            "membership_application_document",
            "sepa_mandate_document",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_front_image"].required = True
        self.fields["id_back_image"].required = True
        self.fields["membership_application_document"].required = False
        self.fields["sepa_mandate_document"].required = False
        for field in self.fields.values():
            _apply_form_control(field.widget)

    def _validate_upload_size(self, upload, label: str):
        if upload and upload.size > self.MAX_UPLOAD_SIZE:
            raise ValidationError(f"{label} darf maximal 5 MB gross sein.")

    def clean_id_front_image(self):
        upload = self.cleaned_data.get("id_front_image")
        self._validate_upload_size(upload, "Vorderseite")
        if upload and not (upload.content_type or "").startswith("image/"):
            raise ValidationError("Bitte eine Bilddatei fuer die Vorderseite hochladen.")
        return upload

    def clean_id_back_image(self):
        upload = self.cleaned_data.get("id_back_image")
        self._validate_upload_size(upload, "Rueckseite")
        if upload and not (upload.content_type or "").startswith("image/"):
            raise ValidationError("Bitte eine Bilddatei fuer die Rueckseite hochladen.")
        return upload

    def clean_membership_application_document(self):
        upload = self.cleaned_data.get("membership_application_document")
        self._validate_upload_size(upload, "Aufnahmeantrag")
        return upload

    def clean_sepa_mandate_document(self):
        upload = self.cleaned_data.get("sepa_mandate_document")
        self._validate_upload_size(upload, "SEPA-Lastschriftmandat")
        return upload
