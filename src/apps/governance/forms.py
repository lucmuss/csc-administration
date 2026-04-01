from datetime import datetime, timedelta
from urllib.parse import urlparse

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.members.models import Profile

from .models import (
    AuditLog,
    BoardMeeting,
    BoardTask,
    IntegrationEndpoint,
    MeetingAgendaItem,
    MeetingResolution,
    OperationalRecord,
)


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                continue
            classes = widget.attrs.get("class", "")
            suffix = " form-input form-select" if isinstance(widget, forms.Select) else " form-input"
            widget.attrs["class"] = (classes + suffix).strip()


class BoardMeetingForm(StyledModelForm):
    scheduled_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "data-date-picker": "true",
            }
        ),
        label="Datum",
    )
    scheduled_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                "type": "time",
                "step": "60",
                "data-time-picker": "true",
            }
        ),
        label="Uhrzeit",
    )

    class Meta:
        model = BoardMeeting
        fields = [
            "title",
            "meeting_type",
            "location",
            "participation_url",
            "minutes_url",
            "agenda_submission_email",
            "invitation_lead_days",
            "reminder_lead_hours",
            "chairperson",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].label = "Titel"
        self.fields["meeting_type"].label = "Sitzungstyp"
        self.fields["location"].label = "Ort oder Raum"
        self.fields["participation_url"].label = "Teilnahme-Link"
        self.fields["minutes_url"].label = "Protokoll-Link"
        self.fields["minutes_url"].help_text = "Optionaler Link zum fertigen Protokoll oder zum Dokumentenordner."
        self.fields["agenda_submission_email"].label = "E-Mail fuer Tagesordnungspunkte"
        self.fields["invitation_lead_days"].label = "Einladung vorher (Tage)"
        self.fields["reminder_lead_hours"].label = "Reminder vorher (Stunden)"
        self.fields["chairperson"].label = "Leitung"
        self.fields["scheduled_date"].help_text = "Waehle den Kalendertag der Sitzung."
        self.fields["scheduled_time"].help_text = "Waehle die geplante Startzeit."

        scheduled_for = None
        if self.instance.pk and self.instance.scheduled_for:
            scheduled_for = timezone.localtime(self.instance.scheduled_for)
        elif self.initial.get("scheduled_for"):
            scheduled_for = self.initial["scheduled_for"]

        if scheduled_for:
            if timezone.is_aware(scheduled_for):
                scheduled_for = timezone.localtime(scheduled_for)
            self.fields["scheduled_date"].initial = scheduled_for.date()
            self.fields["scheduled_time"].initial = scheduled_for.strftime("%H:%M")

    def clean(self):
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get("scheduled_date")
        scheduled_time = cleaned_data.get("scheduled_time")
        if not scheduled_date or not scheduled_time:
            return cleaned_data

        scheduled_for = timezone.make_aware(datetime.combine(scheduled_date, scheduled_time), timezone.get_current_timezone())
        cleaned_data["scheduled_for"] = scheduled_for
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.scheduled_for = self.cleaned_data["scheduled_for"]
        if commit:
            instance.save()
        return instance


class MeetingAgendaItemForm(StyledModelForm):
    class Meta:
        model = MeetingAgendaItem
        fields = ["order", "title", "description", "owner", "planned_duration_minutes", "status"]


class MeetingResolutionForm(StyledModelForm):
    class Meta:
        model = MeetingResolution
        fields = ["agenda_item", "title", "decision_text", "status", "vote_result"]


class BoardTaskForm(StyledModelForm):
    class Meta:
        model = BoardTask
        fields = ["title", "description", "priority", "status", "due_date", "owner"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].label = "Aufgabentitel"
        self.fields["description"].label = "Beschreibung"
        self.fields["priority"].label = "Prioritaet"
        self.fields["status"].label = "Status"
        self.fields["due_date"].label = "Faellig am"
        self.fields["owner"].label = "Verantwortlich"
        self.fields["due_date"].initial = self.fields["due_date"].initial or (timezone.localdate() + timedelta(days=5))


class MemberCardIssueForm(forms.Form):
    profile = forms.ModelChoiceField(
        queryset=Profile.objects.select_related("user")
        .filter(status__in=[Profile.STATUS_VERIFIED, Profile.STATUS_ACTIVE])
        .order_by("member_number", "user__last_name"),
        label="Mitglied",
    )
    expires_at = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Gueltig bis")
    notes = forms.CharField(required=False, widget=forms.Textarea, label="Hinweise")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (classes + " form-input").strip()


class OperationalRecordForm(StyledModelForm):
    class Meta:
        model = OperationalRecord
        fields = [
            "record_type",
            "strain",
            "related_member",
            "quantity_grams",
            "origin",
            "destination",
            "operator_name",
            "witness_name",
            "vehicle_identifier",
            "destruction_method",
            "notes",
        ]


class IntegrationEndpointForm(StyledModelForm):
    subscribed_events_input = forms.CharField(required=False, label="Webhook-Events", help_text="Kommagetrennt, z. B. governance.task.updated, finance.mandate.created")
    resource_scope_input = forms.CharField(required=False, label="API-Ressourcen", help_text="Kommagetrennt, z. B. members,invoices,tasks,records")

    class Meta:
        model = IntegrationEndpoint
        fields = [
            "name",
            "integration_type",
            "endpoint_url",
            "auth_header_name",
            "auth_token",
            "enabled",
        ]
        widgets = {
            "auth_token": forms.PasswordInput(render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["subscribed_events_input"].initial = ", ".join(self.instance.subscribed_events)
            self.fields["resource_scope_input"].initial = ", ".join(self.instance.resource_scope)
        self.fields["enabled"].widget.attrs["class"] = ""
        self.fields["endpoint_url"].help_text = (
            "Webhook-Ziel muss aus dem Docker-Container erreichbar sein, z. B. per LAN-IP oder "
            "host.docker.internal statt 127.0.0.1."
        )
        self.fields["endpoint_url"].widget.attrs["placeholder"] = "https://buchhaltung.example/api/csc/webhook"
        self.fields["auth_token"].help_text = "Optionaler Token fuer ausgehende Webhook-Aufrufe."

    def clean_subscribed_events_input(self):
        raw = self.cleaned_data["subscribed_events_input"]
        return [item.strip() for item in raw.split(",") if item.strip()]

    def clean_resource_scope_input(self):
        raw = self.cleaned_data["resource_scope_input"]
        return [item.strip() for item in raw.split(",") if item.strip()]

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise ValidationError("Bitte gib einen Namen fuer die Integration an.")
        if "<" in name or ">" in name:
            raise ValidationError("HTML-Tags sind im Namen nicht erlaubt.")
        return name

    def clean_endpoint_url(self):
        endpoint_url = (self.cleaned_data.get("endpoint_url") or "").strip()
        if not endpoint_url:
            raise ValidationError("Bitte gib eine gueltige Endpoint-URL an.")

        parsed = urlparse(endpoint_url)
        if parsed.scheme not in {"http", "https"}:
            raise ValidationError("Die Endpoint-URL muss mit http:// oder https:// beginnen.")
        if not parsed.netloc:
            raise ValidationError("Die Endpoint-URL braucht einen gueltigen Hostnamen.")

        hostname = (parsed.hostname or "").lower()
        is_local_host = hostname in {"localhost", "host.docker.internal"} or hostname.endswith(".local")
        is_ipv4 = hostname.count(".") == 3 and all(part.isdigit() and 0 <= int(part) <= 255 for part in hostname.split("."))
        if not (is_local_host or is_ipv4 or "." in hostname):
            raise ValidationError("Bitte gib einen vollstaendigen Hostnamen oder eine gueltige LAN-IP an.")
        return endpoint_url

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.subscribed_events = self.cleaned_data["subscribed_events_input"]
        instance.resource_scope = self.cleaned_data["resource_scope_input"]
        if commit:
            instance.save()
        return instance


class AuditLogFilterForm(forms.Form):
    domain = forms.ChoiceField(required=False, choices=[("", "Alle Domaenen")], label="Domaene")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        domains = [(domain, domain.title()) for domain in AuditLog.objects.order_by().values_list("domain", flat=True).distinct()]
        self.fields["domain"].choices += domains
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-input"
