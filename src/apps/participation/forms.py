from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import Shift, WorkHours


class WorkHoursEntryForm(forms.ModelForm):
    class Meta:
        model = WorkHours
        fields = ["date", "hours", "shift", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4, "placeholder": "Kurze Beschreibung deiner Mitwirkung"}),
        }
        labels = {
            "date": "Datum",
            "hours": "Stunden",
            "shift": "Schicht",
            "notes": "Notizen",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hours"].min_value = Decimal("0.50")
        self.fields["hours"].widget.attrs.update({"min": "0.5", "step": "0.5", "inputmode": "decimal"})
        self.fields["hours"].initial = Decimal("1.0")
        self.fields["shift"].queryset = Shift.objects.order_by("starts_at")
        self.fields["shift"].required = False
        self.fields["shift"].empty_label = "Ohne Schichtzuordnung"
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-input form-select"
            else:
                field.widget.attrs["class"] = "form-input"
        self.fields["date"].widget = forms.HiddenInput()
        self.fields["date"].initial = timezone.localdate

    def clean_date(self):
        value = self.cleaned_data["date"]
        if value > timezone.localdate():
            raise forms.ValidationError("Arbeitsstunden koennen nicht in der Zukunft eingetragen werden.")
        return value


class ShiftForm(forms.ModelForm):
    starts_at = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}, format="%Y-%m-%dT%H:%M"),
        label="Beginn",
    )
    ends_at = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}, format="%Y-%m-%dT%H:%M"),
        label="Ende",
    )

    class Meta:
        model = Shift
        fields = ["title", "description", "starts_at", "ends_at", "required_members"]
        labels = {
            "title": "Schichttitel",
            "description": "Beschreibung",
            "required_members": "Benoetigte Personen",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-input form-select"
            else:
                field.widget.attrs["class"] = "form-input"

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get("starts_at")
        ends_at = cleaned_data.get("ends_at")
        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error("ends_at", "Das Ende muss nach dem Beginn liegen.")
        return cleaned_data


class AdminWorkHoursReviewForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ("approve", "Freigeben"),
            ("revoke", "Freigabe entfernen"),
            ("delete", "Eintrag loeschen"),
        ]
    )
