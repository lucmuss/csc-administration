import hashlib
import json
from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_qr_token():
    return uuid4().hex


def default_card_expiry():
    return timezone.localdate() + timedelta(days=365)


def default_api_key():
    return uuid4().hex


class BoardMeeting(models.Model):
    TYPE_BOARD = "board"
    TYPE_GENERAL = "general"
    TYPE_COMMITTEE = "committee"
    TYPE_CHOICES = [
        (TYPE_BOARD, "Vorstandssitzung"),
        (TYPE_GENERAL, "Mitgliederversammlung"),
        (TYPE_COMMITTEE, "Arbeitskreis"),
    ]

    STATUS_PLANNED = "planned"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PLANNED, "Geplant"),
        (STATUS_COMPLETED, "Abgeschlossen"),
        (STATUS_CANCELLED, "Abgesagt"),
    ]

    title = models.CharField(max_length=160)
    meeting_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_BOARD)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNED)
    scheduled_for = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    participation_url = models.URLField(blank=True)
    minutes_url = models.URLField(blank=True)
    agenda_submission_email = models.EmailField(blank=True)
    invitation_lead_days = models.PositiveSmallIntegerField(default=14)
    reminder_lead_hours = models.PositiveSmallIntegerField(default=24)
    invitation_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    minutes_summary = models.TextField(blank=True)
    attendance_notes = models.TextField(blank=True)
    chairperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chaired_meetings",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_meetings",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_for", "-id"]

    def __str__(self):
        return self.title


class MeetingAgendaItem(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_DEFERRED = "deferred"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Offen"),
        (STATUS_CLOSED, "Bearbeitet"),
        (STATUS_DEFERRED, "Vertagt"),
    ]

    meeting = models.ForeignKey(BoardMeeting, on_delete=models.CASCADE, related_name="agenda_items")
    order = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_agenda_items",
    )
    planned_duration_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("meeting", "order")

    def __str__(self):
        return f"{self.meeting.title} / TOP {self.order}"


class MeetingResolution(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ADOPTED = "adopted"
    STATUS_REJECTED = "rejected"
    STATUS_DEFERRED = "deferred"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Entwurf"),
        (STATUS_ADOPTED, "Beschlossen"),
        (STATUS_REJECTED, "Abgelehnt"),
        (STATUS_DEFERRED, "Vertagt"),
    ]

    meeting = models.ForeignKey(BoardMeeting, on_delete=models.CASCADE, related_name="resolutions")
    agenda_item = models.ForeignKey(
        MeetingAgendaItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolutions",
    )
    resolution_number = models.CharField(max_length=40, unique=True, blank=True)
    title = models.CharField(max_length=180)
    decision_text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    vote_result = models.CharField(max_length=120, blank=True)
    adopted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_resolutions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def save(self, *args, **kwargs):
        if not self.resolution_number:
            count = MeetingResolution.objects.filter(meeting=self.meeting).count() + 1
            self.resolution_number = f"RES-{self.meeting_id}-{count:02d}"
        if self.status == self.STATUS_ADOPTED and not self.adopted_at:
            self.adopted_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.resolution_number or self.title


class BoardTask(models.Model):
    STATUS_TODO = "todo"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_BLOCKED = "blocked"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_TODO, "Offen"),
        (STATUS_IN_PROGRESS, "In Arbeit"),
        (STATUS_BLOCKED, "Blockiert"),
        (STATUS_DONE, "Erledigt"),
    ]

    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CRITICAL = "critical"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Niedrig"),
        (PRIORITY_MEDIUM, "Mittel"),
        (PRIORITY_HIGH, "Hoch"),
        (PRIORITY_CRITICAL, "Kritisch"),
    ]

    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="board_tasks",
    )
    related_meeting = models.ForeignKey(
        BoardMeeting,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_board_tasks",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "-created_at"]

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_DONE and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.STATUS_DONE:
            self.completed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class MemberCard(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_REVOKED = "revoked"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Aktiv"),
        (STATUS_REVOKED, "Entzogen"),
        (STATUS_EXPIRED, "Abgelaufen"),
    ]

    profile = models.OneToOneField("members.Profile", on_delete=models.CASCADE, related_name="member_card")
    card_number = models.CharField(max_length=40, unique=True)
    qr_token = models.CharField(max_length=64, unique=True, default=default_qr_token)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_member_cards",
    )
    issued_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateField(default=default_card_expiry)
    last_scanned_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    version = models.PositiveSmallIntegerField(default=1)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["profile__member_number", "profile__user__email"]

    def __str__(self):
        return self.card_number

    @property
    def is_valid(self):
        return self.status == self.STATUS_ACTIVE and self.expires_at >= timezone.localdate()


class OperationalRecord(models.Model):
    TYPE_TRANSPORT = "transport"
    TYPE_DESTRUCTION = "destruction"
    TYPE_CHOICES = [
        (TYPE_TRANSPORT, "Transportnachweis"),
        (TYPE_DESTRUCTION, "Vernichtungsnachweis"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_APPROVED = "approved"
    STATUS_EXECUTED = "executed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Entwurf"),
        (STATUS_APPROVED, "Freigegeben"),
        (STATUS_EXECUTED, "Durchgefuehrt"),
    ]

    reference = models.CharField(max_length=48, unique=True, blank=True)
    record_type = models.CharField(max_length=24, choices=TYPE_CHOICES)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    strain = models.ForeignKey(
        "inventory.Strain",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operational_records",
    )
    related_member = models.ForeignKey(
        "members.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operational_records",
    )
    quantity_grams = models.DecimalField(max_digits=10, decimal_places=2)
    origin = models.CharField(max_length=255, blank=True)
    destination = models.CharField(max_length=255, blank=True)
    operator_name = models.CharField(max_length=160, blank=True)
    witness_name = models.CharField(max_length=160, blank=True)
    vehicle_identifier = models.CharField(max_length=80, blank=True)
    destruction_method = models.CharField(max_length=160, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_operational_records",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_operational_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def save(self, *args, **kwargs):
        if not self.reference:
            stamp = timezone.localtime().strftime("%Y%m%d%H%M")
            prefix = "TR" if self.record_type == self.TYPE_TRANSPORT else "VE"
            self.reference = f"{prefix}-{stamp}-{uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_entries",
    )
    domain = models.CharField(max_length=32)
    action = models.CharField(max_length=64)
    target_model = models.CharField(max_length=80, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    summary = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    previous_hash = models.CharField(max_length=64, blank=True, editable=False)
    entry_hash = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["domain", "created_at"])]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("AuditLog ist append-only und darf nicht aktualisiert werden.")
        if not self.entry_hash:
            payload = {
                "created_at": self.created_at.isoformat(),
                "actor": getattr(self.actor, "email", ""),
                "domain": self.domain,
                "action": self.action,
                "target_model": self.target_model,
                "target_id": self.target_id,
                "summary": self.summary,
                "metadata": self.metadata,
                "ip_address": self.ip_address,
                "previous_hash": self.previous_hash,
            }
            self.entry_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.domain}:{self.action}"


class IntegrationEndpoint(models.Model):
    TYPE_BOOKKEEPING = "bookkeeping"
    TYPE_PRINTER = "printer"
    TYPE_EXTERNAL = "external"
    TYPE_CHOICES = [
        (TYPE_BOOKKEEPING, "Buchhaltung"),
        (TYPE_PRINTER, "Drucker / Label"),
        (TYPE_EXTERNAL, "Externe Club-App"),
    ]

    name = models.CharField(max_length=160)
    integration_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_EXTERNAL)
    endpoint_url = models.URLField(blank=True)
    api_key = models.CharField(max_length=64, unique=True, default=default_api_key)
    auth_header_name = models.CharField(max_length=64, default="Authorization")
    auth_token = models.CharField(max_length=255, blank=True)
    subscribed_events = models.JSONField(default=list, blank=True)
    resource_scope = models.JSONField(default=list, blank=True)
    enabled = models.BooleanField(default=True)
    last_delivery_at = models.DateTimeField(null=True, blank=True)
    last_delivery_status = models.CharField(max_length=120, blank=True)
    last_error = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_integrations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class IntegrationDelivery(models.Model):
    endpoint = models.ForeignKey(IntegrationEndpoint, on_delete=models.CASCADE, related_name="deliveries")
    event_name = models.CharField(max_length=120)
    payload = models.JSONField(default=dict, blank=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    response_excerpt = models.CharField(max_length=255, blank=True)
    delivered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-delivered_at", "-id"]

    def __str__(self):
        return f"{self.endpoint.name} / {self.event_name}"
