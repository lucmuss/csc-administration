from datetime import date, timedelta
import json
import re
from urllib.request import Request, urlopen

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
PHONE_CODE_CHOICES = [
    ("+49", "Deutschland (+49)"),
    ("+43", "Oesterreich (+43)"),
    ("+41", "Schweiz (+41)"),
    ("+31", "Niederlande (+31)"),
    ("+32", "Belgien (+32)"),
    ("+33", "Frankreich (+33)"),
    ("+34", "Spanien (+34)"),
    ("+39", "Italien (+39)"),
    ("+44", "Vereinigtes Koenigreich (+44)"),
    ("+48", "Polen (+48)"),
    ("+1", "USA/Kanada (+1)"),
]


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


def _normalize_bank_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", (value or "").lower())


def _lookup_iban_bank_data(iban: str) -> dict[str, str]:
    if not getattr(settings, "IBAN_API_VALIDATION_ENABLED", False):
        return {}
    endpoint = str(getattr(settings, "IBAN_API_VALIDATION_ENDPOINT", "") or "").strip()
    if not endpoint:
        return {}
    request_url = endpoint.format(iban=iban)
    request = Request(request_url, headers={"User-Agent": "CSC-IBAN-Validation/1.0"})
    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        # Kein Hard-Fail bei externer API-Stoerung: lokale IBAN/BIC-Checks bleiben aktiv.
        return {}
    if payload.get("valid") is False:
        raise forms.ValidationError("Die IBAN wurde von der Bank-API als ungueltig zurueckgemeldet.")
    bank_data = payload.get("bankData") or payload.get("bank_data") or {}
    return {
        "bic": str(bank_data.get("bic", "") or "").strip().upper(),
        "bank_name": str(bank_data.get("name", "") or "").strip(),
    }


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
    return timezone.localdate()


def _split_phone_number(value: str) -> tuple[str, str]:
    normalized = (value or "").strip().replace(" ", "")
    if not normalized:
        return "+49", ""
    for code, _label in PHONE_CODE_CHOICES:
        if normalized.startswith(code):
            return code, normalized[len(code):]
    if normalized.startswith("+"):
        digits = "+" + "".join(ch for ch in normalized if ch.isdigit())
        if len(digits) > 1:
            return digits, ""
    return "+49", normalized


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
    accept_terms = forms.BooleanField(
        required=True,
        label="Ich akzeptiere die Nutzungsbedingungen.",
        error_messages={"required": "Bitte akzeptiere die Nutzungsbedingungen."},
    )

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
        self.fields["email"].error_messages.setdefault("required", "Dieses Feld ist erforderlich.")
        self.fields["first_name"].error_messages.setdefault("required", "Dieses Feld ist erforderlich.")
        self.fields["last_name"].error_messages.setdefault("required", "Dieses Feld ist erforderlich.")
        self.fields["birth_date"].error_messages.setdefault("required", "Dieses Feld ist erforderlich.")
        self.fields["password"].error_messages.setdefault("required", "Dieses Feld ist erforderlich.")
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
    street_address = forms.CharField(max_length=255, label="Strasse")
    street_address_number = forms.CharField(max_length=20, label="Hausnummer")
    postal_code = forms.CharField(max_length=10, label="Postleitzahl")
    city = forms.CharField(max_length=120, label="Stadt")
    phone_country_code = forms.ChoiceField(
        choices=PHONE_CODE_CHOICES,
        label="Laendervorwahl",
        initial="+49",
        required=False,
    )
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
        self._iban_api_data = {}
        super().__init__(*args, **kwargs)
        active_mandate = profile.sepa_mandate or SepaMandate.objects.filter(profile=profile, is_active=True).first()
        self.fields["desired_join_date"].initial = profile.desired_join_date or _default_join_date()
        address = (profile.street_address or "").strip()
        match = re.match(r"^(?P<street>.*\D)\s+(?P<number>\d+[A-Za-z0-9\-\/]*)$", address)
        if match:
            self.fields["street_address"].initial = match.group("street").strip()
            self.fields["street_address_number"].initial = match.group("number").strip()
        else:
            self.fields["street_address"].initial = address
        self.fields["postal_code"].initial = profile.postal_code
        self.fields["city"].initial = profile.city
        code, local_number = _split_phone_number(profile.phone)
        self.fields["phone_country_code"].initial = code
        self.fields["phone"].initial = local_number or profile.phone
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
        self.fields["phone_country_code"].widget.attrs.setdefault("autocomplete", "tel-country-code")
        self.fields["phone"].widget.attrs.setdefault("autocomplete", "tel-national")
        self.fields["phone"].widget.attrs.setdefault("inputmode", "tel")
        self.fields["phone"].widget.attrs.setdefault("placeholder", "15112345678")
        self.fields["street_address"].widget.attrs.setdefault("autocomplete", "street-address")
        self.fields["street_address_number"].widget.attrs.setdefault("autocomplete", "address-line2")
        self.fields["street_address_number"].widget.attrs.setdefault("placeholder", "12a")
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

    def clean_street_address_number(self):
        value = (self.cleaned_data.get("street_address_number") or "").strip()
        if not value:
            street_value = (self.cleaned_data.get("street_address") or "").strip()
            match = re.match(r"^(?P<street>.*\D)\s+(?P<number>\d+[A-Za-z0-9\-\/]*)$", street_value)
            if match:
                self.cleaned_data["street_address"] = match.group("street").strip()
                value = match.group("number").strip()
        if not value:
            raise forms.ValidationError("Bitte eine Hausnummer eingeben.")
        if not re.fullmatch(r"^\d{1,5}[A-Za-z]?[A-Za-z0-9\-\/]*$", value):
            raise forms.ValidationError("Bitte eine gueltige Hausnummer eingeben.")
        return value

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip().replace(" ", "")
        if not phone:
            raise forms.ValidationError("Bitte eine Telefonnummer eingeben.")
        if phone.startswith("+"):
            allowed = set("+0123456789")
            if any(char not in allowed for char in phone):
                raise forms.ValidationError("Bitte nur Zahlen und optional ein Pluszeichen verwenden.")
            return phone
        if not phone.isdigit():
            raise forms.ValidationError("Bitte nur Zahlen eingeben.")
        if len(phone) < 6:
            raise forms.ValidationError("Die Telefonnummer ist zu kurz.")
        return phone

    def clean_phone_country_code(self):
        code = (self.cleaned_data.get("phone_country_code") or "").strip()
        if not code:
            return "+49"
        if not code.startswith("+") or not code[1:].isdigit():
            raise forms.ValidationError("Bitte eine gueltige Laendervorwahl auswaehlen.")
        return code

    def clean(self):
        cleaned_data = super().clean()
        phone = (cleaned_data.get("phone") or "").strip().replace(" ", "")
        if phone and not phone.startswith("+"):
            cleaned_data["phone"] = f"{cleaned_data.get('phone_country_code', '+49')}{phone}"
        street = (cleaned_data.get("street_address") or "").strip()
        number = (cleaned_data.get("street_address_number") or "").strip()
        if street and number:
            cleaned_data["street_address"] = f"{street} {number}"
        return cleaned_data

    def clean_iban(self):
        iban = _validate_iban(self.cleaned_data["iban"])
        self._iban_api_data = _lookup_iban_bank_data(iban)
        return iban

    def clean_bic(self):
        bic = _validate_bic(self.cleaned_data["bic"])
        expected_bic = self._iban_api_data.get("bic", "")
        if expected_bic and bic != expected_bic:
            raise forms.ValidationError(f"BIC passt nicht zur IBAN. Erwartet: {expected_bic}")
        return bic

    def clean_bank_name(self):
        bank_name = _validate_bank_name(self.cleaned_data["bank_name"])
        expected_name = self._iban_api_data.get("bank_name", "")
        if expected_name:
            expected_norm = _normalize_bank_name(expected_name)
            provided_norm = _normalize_bank_name(bank_name)
            if expected_norm and provided_norm and expected_norm not in provided_norm and provided_norm not in expected_norm:
                raise forms.ValidationError(
                    f"Bankname passt nicht zur IBAN-API. Erwartet z. B.: {expected_name}"
                )
        return bank_name

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
    phone_country_code = forms.ChoiceField(
        choices=PHONE_CODE_CHOICES,
        label="Laendervorwahl",
        initial="+49",
        required=False,
    )
    phone = forms.CharField(max_length=32, label="Telefonnummer")
    street_address = forms.CharField(max_length=255, label="Strasse", required=False)
    street_address_number = forms.CharField(max_length=20, label="Hausnummer", required=False)
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
        self._iban_api_data = {}
        super().__init__(*args, **kwargs)
        mandate = profile.sepa_mandate or SepaMandate.objects.filter(profile=profile, is_active=True).first()
        self.fields["first_name"].initial = profile.user.first_name
        self.fields["last_name"].initial = profile.user.last_name
        self.fields["email"].initial = profile.user.email
        code, local_number = _split_phone_number(profile.phone)
        self.fields["phone_country_code"].initial = code
        self.fields["phone"].initial = local_number or profile.phone
        address = (profile.street_address or "").strip()
        match = re.match(r"^(?P<street>.*\D)\s+(?P<number>\d+[A-Za-z0-9\-\/]*)$", address)
        if match:
            self.fields["street_address"].initial = match.group("street").strip()
            self.fields["street_address_number"].initial = match.group("number").strip()
        else:
            self.fields["street_address"].initial = address
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
        self.fields["phone_country_code"].widget.attrs.setdefault("autocomplete", "tel-country-code")
        self.fields["phone"].widget.attrs.setdefault("autocomplete", "tel-national")
        self.fields["phone"].widget.attrs.setdefault("inputmode", "tel")
        self.fields["phone"].widget.attrs.setdefault("placeholder", "15112345678")
        self.fields["street_address"].widget.attrs.setdefault("autocomplete", "street-address")
        self.fields["street_address_number"].widget.attrs.setdefault("autocomplete", "address-line2")
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

    def clean_street_address_number(self):
        value = (self.cleaned_data.get("street_address_number") or "").strip()
        if value and not re.fullmatch(r"^\d{1,5}[A-Za-z]?[A-Za-z0-9\-\/]*$", value):
            raise forms.ValidationError("Bitte eine gueltige Hausnummer eingeben.")
        return value

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip().replace(" ", "")
        if not phone:
            raise forms.ValidationError("Bitte eine Telefonnummer eingeben.")
        if phone.startswith("+"):
            allowed = set("+0123456789")
            if any(char not in allowed for char in phone):
                raise forms.ValidationError("Bitte nur Zahlen und optional ein Pluszeichen verwenden.")
            return phone
        if not phone.isdigit():
            raise forms.ValidationError("Bitte nur Zahlen eingeben.")
        if len(phone) < 6:
            raise forms.ValidationError("Die Telefonnummer ist zu kurz.")
        return phone

    def clean_phone_country_code(self):
        code = (self.cleaned_data.get("phone_country_code") or "").strip()
        if not code:
            return "+49"
        if not code.startswith("+") or not code[1:].isdigit():
            raise forms.ValidationError("Bitte eine gueltige Laendervorwahl auswaehlen.")
        return code

    def clean(self):
        cleaned_data = super().clean()
        phone = (cleaned_data.get("phone") or "").strip().replace(" ", "")
        if phone and not phone.startswith("+"):
            cleaned_data["phone"] = f"{cleaned_data.get('phone_country_code', '+49')}{phone}"
        street = (cleaned_data.get("street_address") or "").strip()
        number = (cleaned_data.get("street_address_number") or "").strip()
        if street and number:
            cleaned_data["street_address"] = f"{street} {number}"
        return cleaned_data

    def clean_iban(self):
        iban = _validate_iban(self.cleaned_data["iban"])
        self._iban_api_data = _lookup_iban_bank_data(iban)
        return iban

    def clean_bic(self):
        bic = _validate_bic(self.cleaned_data["bic"])
        expected_bic = self._iban_api_data.get("bic", "")
        if expected_bic and bic != expected_bic:
            raise forms.ValidationError(f"BIC passt nicht zur IBAN. Erwartet: {expected_bic}")
        return bic

    def clean_bank_name(self):
        bank_name = _validate_bank_name(self.cleaned_data["bank_name"])
        expected_name = self._iban_api_data.get("bank_name", "")
        if expected_name:
            expected_norm = _normalize_bank_name(expected_name)
            provided_norm = _normalize_bank_name(bank_name)
            if expected_norm and provided_norm and expected_norm not in provided_norm and provided_norm not in expected_norm:
                raise forms.ValidationError(
                    f"Bankname passt nicht zur IBAN-API. Erwartet z. B.: {expected_name}"
                )
        return bank_name

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
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_front_image"].required = True
        self.fields["id_back_image"].required = True
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
