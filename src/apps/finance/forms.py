from django import forms


class SepaMandateForm(forms.Form):
    iban = forms.CharField(max_length=34, label="IBAN")
    bic = forms.CharField(max_length=11, label="BIC")
    account_holder = forms.CharField(max_length=255, label="Kontoinhaber")
