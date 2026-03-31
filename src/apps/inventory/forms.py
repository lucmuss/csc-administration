from decimal import Decimal, InvalidOperation

from django import forms

from .models import InventoryLocation, Strain


class StrainForm(forms.ModelForm):
    class Meta:
        model = Strain
        fields = [
            "name",
            "product_type",
            "card_tone",
            "image",
            "thc",
            "cbd",
            "price",
            "stock",
            "quality_grade",
            "is_active",
        ]
        labels = {
            "name": "Produktname",
            "product_type": "Produkttyp",
            "card_tone": "Kartenfarbe",
            "image": "Shop-Bild",
            "thc": "THC in %",
            "cbd": "CBD in %",
            "price": "Preis in EUR",
            "stock": "Bestand",
            "quality_grade": "Qualitaetsstufe",
            "is_active": "Im Shop aktiv",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].required = False
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-checkbox"
                continue
            control_class = "form-input form-select" if isinstance(widget, forms.Select) else "form-input"
            widget.attrs["class"] = control_class
            if name in {"thc", "cbd", "price", "stock"}:
                widget.attrs.setdefault("step", "0.01")
        self.fields["stock"].help_text = "Blueten werden in Gramm, Stecklinge und Edibles in Stueck gefuehrt."


class InventoryLocationForm(forms.ModelForm):
    class Meta:
        model = InventoryLocation
        fields = ["name", "type", "capacity"]
        labels = {
            "name": "Lagerort",
            "type": "Typ",
            "capacity": "Kapazitaet",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            control_class = "form-input form-select" if isinstance(widget, forms.Select) else "form-input"
            widget.attrs["class"] = control_class
            if name == "capacity":
                widget.attrs.setdefault("step", "0.01")


class InventoryCountValueField(forms.DecimalField):
    def to_python(self, value):
        parsed = super().to_python(value)
        if parsed is None:
            return None
        try:
            normalized = Decimal(parsed)
        except InvalidOperation as exc:
            raise forms.ValidationError("Bitte eine gueltige ganze Zahl eingeben.") from exc
        if normalized != normalized.to_integral_value():
            raise forms.ValidationError("Inventurwerte muessen als ganze Zahl erfasst werden.")
        return normalized
