# messaging/forms.py
from django import forms
from .models import EmailGroup, MassEmail, SmsMessage, SmsTemplate, SmsProviderConfig
from apps.members.models import Profile
import markdown


class EmailGroupForm(forms.ModelForm):
    """Formular für E-Mail-Gruppen"""
    class Meta:
        model = EmailGroup
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "z.B. 'Aktive Mitglieder'"
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "rows": 3,
                "placeholder": "Beschreibung der Gruppe..."
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            }),
        }


class EmailGroupMemberForm(forms.Form):
    """Formular zum Hinzufügen von Mitgliedern zu einer Gruppe"""
    members = forms.ModelMultipleChoiceField(
        queryset=Profile.objects.filter(status="active").order_by("user__last_name", "user__first_name"),
        widget=forms.SelectMultiple(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
            "size": 10
        }),
        label="Mitglieder auswählen"
    )


class MassEmailForm(forms.ModelForm):
    """Formular für Massen-E-Mails"""
    
    # Dynamische Empfänger-Auswahl
    recipient_type = forms.ChoiceField(
        choices=MassEmail.RECIPIENT_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "h-4 w-4 text-blue-600"}),
        label="Empfänger",
        initial="all"
    )
    
    recipient_group = forms.ModelChoiceField(
        queryset=EmailGroup.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        }),
        label="Gruppe auswählen"
    )
    
    individual_recipients = forms.ModelMultipleChoiceField(
        queryset=Profile.objects.filter(status="active").order_by("user__last_name", "user__first_name"),
        required=False,
        widget=forms.SelectMultiple(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
            "size": 10
        }),
        label="Individuelle Empfänger"
    )

    class Meta:
        model = MassEmail
        fields = ["subject", "content", "recipient_type", "recipient_group", "individual_recipients"]
        widgets = {
            "subject": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Betreff der E-Mail"
            }),
            "content": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono",
                "rows": 15,
                "placeholder": "E-Mail-Inhalt in Markdown...\n\n# Überschrift\n\nHallo {{ first_name }},\n\nIhre Nachricht hier..."
            }),
        }
        labels = {
            "subject": "Betreff",
            "content": "Inhalt (Markdown)",
        }

    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get("recipient_type")
        recipient_group = cleaned_data.get("recipient_group")
        individual_recipients = cleaned_data.get("individual_recipients")

        if recipient_type == "group" and not recipient_group:
            self.add_error("recipient_group", "Bitte wählen Sie eine Gruppe aus.")
        
        if recipient_type == "individual" and not individual_recipients:
            self.add_error("individual_recipients", "Bitte wählen Sie mindestens einen Empfänger aus.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Konvertiere Markdown zu HTML
        if instance.content:
            instance.content_html = markdown.markdown(
                instance.content,
                extensions=["extra", "nl2br"]
            )
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class MassEmailSendForm(forms.Form):
    """Formular zum Absenden einer Massen-E-Mail"""
    confirm_send = forms.BooleanField(
        required=True,
        label="Ich bestätige den Versand dieser E-Mail",
        widget=forms.CheckboxInput(attrs={
            "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        })
    )


# ==================== SMS FORMS ====================

class SmsProviderConfigForm(forms.ModelForm):
    """Formular für SMS-Provider-Konfiguration"""
    class Meta:
        model = SmsProviderConfig
        fields = ["name", "provider", "api_key", "api_secret", "sender_number", "webhook_url", "cost_per_sms", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "z.B. 'Twilio Produktion'"
            }),
            "provider": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            }),
            "api_key": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono",
                "placeholder": "API Key"
            }),
            "api_secret": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono",
                "placeholder": "API Secret (optional)"
            }),
            "sender_number": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "z.B. +49123456789"
            }),
            "webhook_url": forms.URLInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "https://... (für Custom Provider)"
            }),
            "cost_per_sms": forms.NumberInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "step": "0.0001",
                "placeholder": "0.0750"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            }),
        }


class SmsMessageForm(forms.ModelForm):
    """Formular für einzelne SMS"""
    recipient_type = forms.ChoiceField(
        choices=SmsMessage.RECIPIENT_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "h-4 w-4 text-blue-600"}),
        label="Empfänger",
        initial="individual"
    )
    
    recipient_member = forms.ModelChoiceField(
        queryset=Profile.objects.filter(status="active").order_by("user__last_name", "user__first_name"),
        required=False,
        widget=forms.Select(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        }),
        label="Mitglied auswählen"
    )
    
    recipient_group = forms.ModelChoiceField(
        queryset=EmailGroup.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        }),
        label="Gruppe auswählen"
    )
    
    use_template = forms.BooleanField(
        required=False,
        label="Vorlage verwenden",
        widget=forms.CheckboxInput(attrs={
            "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        })
    )
    
    template = forms.ModelChoiceField(
        queryset=SmsTemplate.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        }),
        label="SMS-Vorlage"
    )

    class Meta:
        model = SmsMessage
        fields = ["recipient_type", "recipient_member", "recipient_group", "recipient_phone", "content"]
        widgets = {
            "recipient_phone": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "+49123456789"
            }),
            "content": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "rows": 5,
                "placeholder": "Ihre Nachricht...",
                "maxlength": 1600
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get("recipient_type")
        recipient_member = cleaned_data.get("recipient_member")
        recipient_group = cleaned_data.get("recipient_group")
        recipient_phone = cleaned_data.get("recipient_phone")
        content = cleaned_data.get("content")
        template = cleaned_data.get("template")
        use_template = cleaned_data.get("use_template")

        if recipient_type == "individual":
            if not recipient_member and not recipient_phone:
                self.add_error("recipient_member", "Bitte wählen Sie ein Mitglied oder geben Sie eine Telefonnummer ein.")
        elif recipient_type == "group":
            if not recipient_group:
                self.add_error("recipient_group", "Bitte wählen Sie eine Gruppe aus.")

        if use_template and template:
            # Inhalt wird aus Template generiert
            pass
        elif not content:
            self.add_error("content", "Bitte geben Sie einen Nachrichtentext ein.")

        return cleaned_data


class SmsTemplateForm(forms.ModelForm):
    """Formular für SMS-Vorlagen"""
    class Meta:
        model = SmsTemplate
        fields = ["name", "description", "content", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Name der Vorlage"
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "rows": 2,
                "placeholder": "Beschreibung..."
            }),
            "content": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono",
                "rows": 5,
                "placeholder": "Hallo {{ first_name }}, Ihre Nachricht...",
                "maxlength": 1600
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            }),
        }


class SmsSendForm(forms.Form):
    """Formular zum Absenden einer SMS"""
    confirm_send = forms.BooleanField(
        required=True,
        label="Ich bestätige den Versand dieser SMS",
        widget=forms.CheckboxInput(attrs={
            "class": "h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        })
    )
    provider = forms.ModelChoiceField(
        queryset=SmsProviderConfig.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        }),
        label="SMS-Provider"
    )
