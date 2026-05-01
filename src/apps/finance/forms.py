from decimal import Decimal
import re
from pathlib import Path

from django import forms
from django.conf import settings

from apps.accounts.models import User

from .models import UploadedInvoice


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
        min_amount = Decimal(str(getattr(settings, "BALANCE_TOPUP_MIN_AMOUNT", "1.00")))
        max_amount = Decimal(str(getattr(settings, "BALANCE_TOPUP_MAX_AMOUNT", "500.00")))
        self.fields["preset_amount"].widget.attrs["class"] = "form-input form-select"
        self.fields["amount"].widget.attrs["class"] = "form-input"
        self.fields["amount"].widget.attrs.update(
            {
                "placeholder": "z. B. 25.00",
                "min": str(min_amount),
                "max": str(max_amount),
                "step": "0.01",
                "inputmode": "decimal",
            }
        )

    def clean(self):
        cleaned_data = super().clean()
        preset = cleaned_data.get("preset_amount")
        amount = cleaned_data.get("amount")
        min_amount = Decimal(str(getattr(settings, "BALANCE_TOPUP_MIN_AMOUNT", "1.00")))
        max_amount = Decimal(str(getattr(settings, "BALANCE_TOPUP_MAX_AMOUNT", "500.00")))
        if preset and preset != "custom":
            selected = Decimal(preset)
            if selected < min_amount or selected > max_amount:
                raise forms.ValidationError("Der ausgewaehlte Betrag liegt ausserhalb des erlaubten Bereichs.")
            cleaned_data["amount"] = cleaned_data["selected_amount"] = cleaned_data["final_amount"] = selected
            return cleaned_data
        if amount is None:
            raise forms.ValidationError("Bitte waehle einen Betrag oder gib einen eigenen Betrag ein.")
        if amount < min_amount:
            raise forms.ValidationError(f"Bitte gib mindestens {min_amount} EUR ein.")
        if amount > max_amount:
            raise forms.ValidationError(f"Bitte gib hoechstens {max_amount} EUR ein.")
        cleaned_data["selected_amount"] = cleaned_data["final_amount"] = amount
        return cleaned_data


class UploadedInvoiceForm(forms.ModelForm):
    class Meta:
        model = UploadedInvoice
        fields = ["title", "direction", "document", "payment_status", "assigned_to", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)
        self.fields["title"].required = False
        self.fields["assigned_to"].queryset = User.objects.filter(role__in=[User.ROLE_STAFF, User.ROLE_BOARD]).order_by(
            "first_name",
            "last_name",
            "email",
        )
        if current_user and not self.instance.pk:
            self.fields["assigned_to"].initial = current_user
        self.fields["document"].required = not bool(self.instance and self.instance.pk)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-checkbox"
            else:
                field.widget.attrs["class"] = "form-input form-select" if isinstance(field.widget, forms.Select) else "form-input"
        self.fields["title"].widget.attrs.setdefault("placeholder", "wird automatisch aus der Rechnung ermittelt")

    def clean_document(self):
        document = self.cleaned_data["document"]
        suffix = Path(document.name).suffix.lower()
        allowed = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt"}
        if suffix not in allowed:
            raise forms.ValidationError("Erlaubt sind PDF, JPG, JPEG, PNG, WEBP und TXT.")
        return document


class UploadedInvoiceUpdateForm(forms.ModelForm):
    class Meta:
        model = UploadedInvoice
        fields = [
            "title",
            "direction",
            "invoice_number",
            "vendor_name",
            "customer_name",
            "issue_date",
            "due_date",
            "amount_net",
            "amount_tax",
            "amount_gross",
            "currency",
            "payment_status",
            "paid_at",
            "assigned_to",
            "notes",
        ]
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "paid_at": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(role__in=[User.ROLE_STAFF, User.ROLE_BOARD]).order_by(
            "first_name",
            "last_name",
            "email",
        )
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-input form-select" if isinstance(field.widget, forms.Select) else "form-input"
            if name in {"amount_net", "amount_tax", "amount_gross"}:
                field.widget.attrs.setdefault("step", "0.01")
