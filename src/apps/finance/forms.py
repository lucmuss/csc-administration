from decimal import Decimal
import re

from django import forms


class SepaMandateForm(forms.Form):
    iban = forms.CharField(max_length=34, label="IBAN")
    bic = forms.CharField(max_length=11, label="BIC")
    account_holder = forms.CharField(max_length=255, label="Kontoinhaber")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-input"

    def clean_iban(self):
        iban = re.sub(r"\s+", "", self.cleaned_data["iban"]).upper()
        if not re.fullmatch(r"[A-Z]{2}[0-9A-Z]{13,32}", iban):
            raise forms.ValidationError("Bitte gib eine gueltige IBAN ein.")
        return iban

    def clean_bic(self):
        bic = re.sub(r"\s+", "", self.cleaned_data["bic"]).upper()
        if not re.fullmatch(r"[A-Z0-9]{8}([A-Z0-9]{3})?", bic):
            raise forms.ValidationError("Bitte gib einen gueltigen BIC ein.")
        return bic

    def clean_account_holder(self):
        account_holder = self.cleaned_data["account_holder"].strip()
        if len(account_holder) < 3:
            raise forms.ValidationError("Bitte gib den vollstaendigen Kontoinhaber an.")
        return account_holder


class BalanceTopUpForm(forms.Form):
    PRESET_CHOICES = [
        ("5.00", "5 EUR"),
        ("10.00", "10 EUR"),
        ("20.00", "20 EUR"),
        ("25.00", "25 EUR"),
        ("40.00", "40 EUR"),
        ("50.00", "50 EUR"),
        ("100.00", "100 EUR"),
        ("150.00", "150 EUR"),
        ("custom", "Eigener Betrag"),
    ]
    preset_amount = forms.ChoiceField(
        choices=PRESET_CHOICES,
        initial="25.00",
        label="Schnellauswahl",
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        initial="25.00",
        label="Aufladebetrag",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["preset_amount"].widget.attrs["class"] = "form-input form-select"
        self.fields["amount"].widget.attrs["class"] = "form-input"
        self.fields["amount"].widget.attrs.update(
            {
                "placeholder": "z. B. 25.00",
                "min": "1",
                "step": "0.01",
                "inputmode": "decimal",
            }
        )

    def clean(self):
        cleaned_data = super().clean()
        preset = cleaned_data.get("preset_amount")
        amount = cleaned_data.get("amount")
        if preset and preset != "custom":
            selected = Decimal(preset)
            cleaned_data["amount"] = cleaned_data["selected_amount"] = cleaned_data["final_amount"] = selected
            return cleaned_data
        if amount is None:
            raise forms.ValidationError("Bitte waehle einen Betrag oder gib einen eigenen Betrag ein.")
        if amount <= 0:
            raise forms.ValidationError("Bitte gib einen positiven Betrag ein.")
        cleaned_data["selected_amount"] = cleaned_data["final_amount"] = amount
        return cleaned_data
