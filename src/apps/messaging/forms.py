# messaging/forms.py
from django import forms
from .models import EmailGroup, MassEmail
from apps.members.models import Member
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
        queryset=Member.objects.filter(status="active").order_by("last_name", "first_name"),
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
        queryset=Member.objects.filter(status="active").order_by("last_name", "first_name"),
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
