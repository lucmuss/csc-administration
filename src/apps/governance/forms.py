from django import forms

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
            widget.attrs["class"] = (classes + " form-input").strip()


class BoardMeetingForm(StyledModelForm):
    scheduled_for = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        label="Termin",
    )

    class Meta:
        model = BoardMeeting
        fields = ["title", "meeting_type", "scheduled_for", "location", "chairperson"]


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
        fields = ["title", "description", "priority", "status", "due_date", "owner", "related_meeting"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


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
