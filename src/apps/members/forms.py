from datetime import date

from django import forms
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User

from .models import Profile


class MemberRegistrationForm(forms.Form):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("E-Mail ist bereits registriert")
        return email

    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        today = date.today()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        if age < 21:
            raise forms.ValidationError("Mindestens 21 Jahre erforderlich")
        return birth_date

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self) -> User:
        user = User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            role=User.ROLE_MEMBER,
        )
        profile = Profile.objects.create(
            user=user,
            birth_date=self.cleaned_data["birth_date"],
            monthly_counter_key=date.today().strftime("%Y-%m"),
        )
        profile.full_clean()
        profile.save()
        return user
