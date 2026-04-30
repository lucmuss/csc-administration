from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm

from apps.core.models import SocialClub


def _apply_form_control(widget: forms.Widget) -> None:
    existing_classes = widget.attrs.get("class", "").strip()
    control_class = "form-checkbox" if isinstance(widget, forms.CheckboxInput) else "form-input"
    widget.attrs["class"] = " ".join(part for part in [existing_classes, control_class] if part)


class EmailAuthenticationForm(AuthenticationForm):
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
        selected_state = ""
        if self.is_bound:
            selected_state = (self.data.get("federal_state") or "").strip()
        if not selected_state:
            selected_state = (self.initial.get("federal_state") or "").strip()
        if selected_state:
            self.fields["social_club"].queryset = self.fields["social_club"].queryset.filter(federal_state=selected_state)
        self.fields["username"].widget.attrs.setdefault("inputmode", "email")
        self.fields["password"].widget.attrs.setdefault("autocomplete", "current-password")
        self.fields["password"].widget.attrs.setdefault("placeholder", "Passwort")
        for field in self.fields.values():
            _apply_form_control(field.widget)

    def clean(self):
        cleaned = super().clean()
        user = self.get_user()
        selected_club = cleaned.get("social_club")
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
