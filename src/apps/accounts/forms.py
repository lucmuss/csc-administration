from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="E-Mail", widget=forms.EmailInput(attrs={"autofocus": True}))
