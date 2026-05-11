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
            "cbg",
            "cbn",
            "cbc",
            "cbv",
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
            "cbg": "CBG in %",
            "cbn": "CBN in %",
            "cbc": "CBC in %",
            "cbv": "CBV in %",
            "price": "Preis in EUR",
            "stock": "Bestand",
            "quality_grade": "Qualitaetsstufe",
            "is_active": "Im Shop aktiv",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].required = False
        self.fields["product_type"].choices = [
            (Strain.PRODUCT_TYPE_FLOWER, "Bluete"),
            (Strain.PRODUCT_TYPE_CUTTING, "Steckling"),
            (Strain.PRODUCT_TYPE_ACCESSORY, "Rauchzubehoer"),
            (Strain.PRODUCT_TYPE_MERCH, "Werbegeschenk"),
        ]
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-checkbox"
                continue
            control_class = "form-input form-select" if isinstance(widget, forms.Select) else "form-input"
            widget.attrs["class"] = control_class
            if name in {"thc", "cbd", "cbg", "cbn", "cbc", "cbv", "price", "stock"}:
                widget.attrs.setdefault("step", "0.01")
            if name in {"thc", "cbd", "cbg", "cbn", "cbc", "cbv"}:
                widget.attrs.setdefault("min", "0")
                widget.attrs.setdefault("max", "30")
                widget.attrs.setdefault("inputmode", "decimal")
        self.fields["stock"].help_text = "Blueten werden in Gramm, Stecklinge, Zubehoer und Werbeartikel in Stueck gefuehrt."

    def _validate_cannabinoid_percentage(self, field_name: str, label: str, allow_blank: bool) -> Decimal | None:
        value = self.cleaned_data.get(field_name)
        if value in (None, ""):
            if allow_blank:
                return None
            raise forms.ValidationError(f"{label} ist erforderlich.")
        value = Decimal(value)
        if value < Decimal("0") or value > Decimal("30"):
            raise forms.ValidationError(f"{label} darf nur zwischen 0 und 30 Prozent liegen.")
        return value

    def clean_thc(self):
        return self._validate_cannabinoid_percentage("thc", "THC", allow_blank=False)

    def clean_cbd(self):
        return self._validate_cannabinoid_percentage("cbd", "CBD", allow_blank=False)

    def clean_cbg(self):
        return self._validate_cannabinoid_percentage("cbg", "CBG", allow_blank=True)

    def clean_cbn(self):
        return self._validate_cannabinoid_percentage("cbn", "CBN", allow_blank=True)

    def clean_cbc(self):
        return self._validate_cannabinoid_percentage("cbc", "CBC", allow_blank=True)

    def clean_cbv(self):
        return self._validate_cannabinoid_percentage("cbv", "CBV", allow_blank=True)


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
