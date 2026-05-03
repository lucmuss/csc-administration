from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.db.utils import OperationalError, ProgrammingError

from apps.core.club import (
    ACTIVE_FEDERAL_STATE_COOKIE,
    ACTIVE_FEDERAL_STATE_SESSION_KEY,
    ACTIVE_SOCIAL_CLUB_COOKIE,
    ACTIVE_SOCIAL_CLUB_SESSION_KEY,
)
from apps.core.models import SocialClub


def _apply_form_control(widget: forms.Widget) -> None:
    existing_classes = widget.attrs.get("class", "").strip()
    control_class = "form-checkbox" if isinstance(widget, forms.CheckboxInput) else "form-input"
    widget.attrs["class"] = " ".join(part for part in [existing_classes, control_class] if part)


class EmailAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "E-Mail-Adresse oder Passwort ist falsch.",
        "inactive": "Dieses Konto ist deaktiviert.",
    }

    federal_state = forms.ChoiceField(
        choices=[("", "Bundesland auswaehlen")] + SocialClub.FEDERAL_STATE_CHOICES,
        required=False,
        label="Bundesland",
    )
    social_club = forms.ModelChoiceField(
        queryset=SocialClub.objects.filter(is_active=True, is_approved=True).order_by("name"),
        required=False,
        empty_label="Social Club auswaehlen",
        label="Social Club",
    )
    username = forms.EmailField(
        label="E-Mail",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email", "placeholder": "name@beispiel.de"}),
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self._request = request
        self.fields["username"].error_messages.setdefault("required", "Dieses Feld ist erforderlich.")
        self.fields["password"].error_messages.setdefault("required", "Dieses Feld ist erforderlich.")
        try:
            social_club_queryset = SocialClub.objects.filter(is_active=True, is_approved=True).order_by("name")
            # Trigger a tiny evaluation so tests without DB access can fall back cleanly.
            list(social_club_queryset[:1])
        except (RuntimeError, OperationalError, ProgrammingError):
            social_club_queryset = SocialClub.objects.none()
        if "social_club" in self.fields:
            self.fields["social_club"].queryset = social_club_queryset

        has_saved_club = False
        has_saved_state = False
        if request is not None:
            has_saved_club = bool(request.session.get(ACTIVE_SOCIAL_CLUB_SESSION_KEY) or request.COOKIES.get(ACTIVE_SOCIAL_CLUB_COOKIE))
            has_saved_state = bool(request.session.get(ACTIVE_FEDERAL_STATE_SESSION_KEY) or request.COOKIES.get(ACTIVE_FEDERAL_STATE_COOKIE))
        # Keep the state selector visible while the club selector is still visible.
        # Otherwise a stale saved state can lock users into an empty club list.
        if has_saved_state and has_saved_club:
            self.fields.pop("federal_state", None)
        if has_saved_club:
            self.fields.pop("social_club", None)

        selected_state = ""
        if self.is_bound:
            selected_state = (self.data.get("federal_state") or "").strip()
        if not selected_state:
            selected_state = (self.initial.get("federal_state") or "").strip()
        if selected_state and "social_club" in self.fields:
            filtered = self.fields["social_club"].queryset.filter(federal_state=selected_state)
            if filtered.exists():
                self.fields["social_club"].queryset = filtered
        self.fields["username"].widget.attrs.setdefault("inputmode", "email")
        self.fields["password"].widget.attrs.setdefault("autocomplete", "current-password")
        self.fields["password"].widget.attrs.setdefault("placeholder", "Passwort")
        for field in self.fields.values():
            _apply_form_control(field.widget)

    def clean(self):
        cleaned = super().clean()
        user = self.get_user()
        selected_club = cleaned.get("social_club") if "social_club" in self.fields else None
        if user and selected_club and not user.is_superuser and user.social_club_id != selected_club.id:
            raise forms.ValidationError("Dieses Konto gehoert nicht zum ausgewaehlten Social Club.")
        return cleaned


class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.setdefault("autocomplete", "email")
        self.fields["email"].widget.attrs.setdefault("placeholder", "name@beispiel.de")
        _apply_form_control(self.fields["email"].widget)


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        for field in self.fields.values():
            _apply_form_control(field.widget)
            field.widget.attrs.setdefault("autocomplete", "new-password")
