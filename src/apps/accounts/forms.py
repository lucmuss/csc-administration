from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm


def _apply_form_control(widget: forms.Widget) -> None:
    existing_classes = widget.attrs.get("class", "").strip()
    control_class = "form-checkbox" if isinstance(widget, forms.CheckboxInput) else "form-input"
    widget.attrs["class"] = " ".join(part for part in [existing_classes, control_class] if part)


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-Mail",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email", "placeholder": "name@beispiel.de"}),
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].widget.attrs.setdefault("inputmode", "email")
        self.fields["password"].widget.attrs.setdefault("autocomplete", "current-password")
        self.fields["password"].widget.attrs.setdefault("placeholder", "Passwort")
        for field in self.fields.values():
            _apply_form_control(field.widget)


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
