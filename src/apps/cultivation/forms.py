# cultivation/forms.py
from datetime import date
from decimal import Decimal

from django import forms
from django.core.validators import MinValueValidator

from .models import GrowCycle, Plant, PlantLog, HarvestBatch
from apps.members.models import Profile
from apps.inventory.models import Strain


def _apply_control_classes(field: forms.Field) -> None:
    widget = field.widget
    existing = widget.attrs.get("class", "")
    if isinstance(widget, forms.Select):
        widget.attrs["class"] = f"{existing} form-input form-select".strip()
    elif isinstance(widget, forms.Textarea):
        widget.attrs["class"] = f"{existing} form-input form-textarea".strip()
    else:
        widget.attrs["class"] = f"{existing} form-input".strip()


class GrowCycleForm(forms.ModelForm):
    """Formular für Grow Cycles"""
    
    class Meta:
        model = GrowCycle
        fields = [
            "name", "description", "start_date", "expected_harvest_date",
            "responsible_member", "location", "notes"
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "placeholder": "z.B. 'Grow Q1 2025'"
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "rows": 3,
                "placeholder": "Beschreibung des Grow Cycles..."
            }),
            "start_date": forms.DateInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "type": "date"
            }),
            "expected_harvest_date": forms.DateInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "type": "date"
            }),
            "responsible_member": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            }),
            "location": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "placeholder": "z.B. 'Grow-Raum 1'"
            }),
            "notes": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "rows": 4,
                "placeholder": "Notizen..."
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsible_member"].queryset = Profile.objects.filter(
            status="active"
        ).order_by("user__last_name", "user__first_name")
        self.fields["name"].help_text = "Pflichtfeld, z. B. ein Quartal oder ein Raumbezug."
        self.fields["start_date"].help_text = "Das Startdatum darf nicht in der Vergangenheit liegen."
        self.fields["expected_harvest_date"].help_text = "Muss nach dem Startdatum liegen."
        self.fields["responsible_member"].help_text = "Optional. Du kannst spaeter immer noch ein verantwortliches Mitglied zuweisen."
        for field in self.fields.values():
            _apply_control_classes(field)

    def clean_name(self):
        value = (self.cleaned_data.get("name") or "").strip()
        if len(value) < 3:
            raise forms.ValidationError("Bitte einen Namen mit mindestens 3 Zeichen angeben.")
        return value

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if start_date and start_date < date.today():
            raise forms.ValidationError("Das Startdatum darf nicht in der Vergangenheit liegen.")
        return start_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        expected_harvest_date = cleaned_data.get("expected_harvest_date")
        if start_date and expected_harvest_date and expected_harvest_date <= start_date:
            self.add_error("expected_harvest_date", "Das erwartete Erntedatum muss nach dem Startdatum liegen.")
        return cleaned_data


class PlantForm(forms.ModelForm):
    """Formular für Pflanzen"""
    
    class Meta:
        model = Plant
        fields = [
            "grow_cycle", "strain", "plant_number", "planting_date",
            "expected_yield_grams", "notes"
        ]
        widgets = {
            "grow_cycle": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            }),
            "strain": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            }),
            "plant_number": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "placeholder": "z.B. '001'"
            }),
            "planting_date": forms.DateInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "type": "date"
            }),
            "expected_yield_grams": forms.NumberInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "step": "0.01",
                "placeholder": "Erwarteter Ertrag in Gramm"
            }),
            "notes": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "rows": 3,
                "placeholder": "Notizen..."
            }),
        }


class PlantLogForm(forms.ModelForm):
    """Formular für Pflanzen-Logs"""
    
    class Meta:
        model = PlantLog
        fields = ["log_type", "date", "notes", "products_used", "performed_by"]
        widgets = {
            "log_type": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            }),
            "date": forms.DateTimeInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "type": "datetime-local"
            }),
            "notes": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "rows": 4,
                "placeholder": "Details zur durchgeführten Arbeit..."
            }),
            "products_used": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "rows": 2,
                "placeholder": "z.B. 'BioBizz Grow, 2ml/L'"
            }),
            "performed_by": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["performed_by"].queryset = Profile.objects.filter(
            status="active"
        ).order_by("user__last_name", "user__first_name")


class HarvestBatchForm(forms.ModelForm):
    """Formular für Ernte-Batches"""
    
    class Meta:
        model = HarvestBatch
        fields = [
            "name", "harvest_date", "plants", "total_weight_fresh",
            "quality_grade", "notes"
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "placeholder": "z.B. 'Ernte Februar 2025'"
            }),
            "harvest_date": forms.DateInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "type": "date"
            }),
            "plants": forms.SelectMultiple(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "size": 8
            }),
            "total_weight_fresh": forms.NumberInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "step": "0.01",
                "placeholder": "Frischgewicht in Gramm"
            }),
            "quality_grade": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            }),
            "notes": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "rows": 3,
                "placeholder": "Notizen zur Ernte..."
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur geerntete Pflanzen anzeigen
        self.fields["plants"].queryset = Plant.objects.filter(
            status__in=[Plant.STATUS_HARVESTED, Plant.STATUS_DRYING, Plant.STATUS_CURING]
        ).select_related("strain", "grow_cycle")


class HarvestBatchUpdateForm(forms.ModelForm):
    """Formular zum Aktualisieren eines Harvest Batches (Trocknung/Aushärtung)"""
    
    class Meta:
        model = HarvestBatch
        fields = [
            "total_weight_dried", "drying_start_date", "drying_end_date",
            "curing_start_date", "curing_end_date", "notes"
        ]
        widgets = {
            "total_weight_dried": forms.NumberInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "step": "0.01",
                "placeholder": "Trockengewicht in Gramm"
            }),
            "drying_start_date": forms.DateInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "type": "date"
            }),
            "drying_end_date": forms.DateInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "type": "date"
            }),
            "curing_start_date": forms.DateInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "type": "date"
            }),
            "curing_end_date": forms.DateInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "type": "date"
            }),
            "notes": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "rows": 3,
                "placeholder": "Notizen..."
            }),
        }


class PlantStatusUpdateForm(forms.ModelForm):
    """Formular zum Aktualisieren des Pflanzen-Status"""
    
    class Meta:
        model = Plant
        fields = ["status", "harvest_date", "actual_yield_grams"]
        widgets = {
            "status": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            }),
            "harvest_date": forms.DateInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "type": "date"
            }),
            "actual_yield_grams": forms.NumberInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                "step": "0.01",
                "placeholder": "Tatsächlicher Ertrag in Gramm"
            }),
        }
