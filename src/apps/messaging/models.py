# messaging/models.py
from django.db import models
from django.contrib.auth import get_user_model
from apps.members.models import Member
import uuid

User = get_user_model()


class EmailGroup(models.Model):
    """E-Mail-Gruppen für Massenversand"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Gruppenname")
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_email_groups"
    )

    class Meta:
        verbose_name = "E-Mail-Gruppe"
        verbose_name_plural = "E-Mail-Gruppen"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()


class EmailGroupMember(models.Model):
    """Zuordnung von Mitgliedern zu E-Mail-Gruppen"""
    group = models.ForeignKey(EmailGroup, on_delete=models.CASCADE, related_name="members")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="email_groups")
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ["group", "member"]
        verbose_name = "Gruppenmitglied"
        verbose_name_plural = "Gruppenmitglieder"


class MassEmail(models.Model):
    """Massen-E-Mail-Versand"""
    STATUS_CHOICES = [
        ("draft", "Entwurf"),
        ("queued", "In Warteschlange"),
        ("sending", "Wird gesendet"),
        ("sent", "Gesendet"),
        ("failed", "Fehlgeschlagen"),
        ("cancelled", "Abgebrochen"),
    ]

    RECIPIENT_TYPE_CHOICES = [
        ("all", "Alle Mitglieder"),
        ("group", "Bestimmte Gruppe"),
        ("individual", "Individuelle Auswahl"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=255, verbose_name="Betreff")
    content = models.TextField(verbose_name="Inhalt (Markdown)")
    content_html = models.TextField(blank=True, verbose_name="Inhalt (HTML)")
    
    # Empfänger
    recipient_type = models.CharField(
        max_length=20, choices=RECIPIENT_TYPE_CHOICES, default="all"
    )
    recipient_group = models.ForeignKey(
        EmailGroup, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Empfängergruppe"
    )
    individual_recipients = models.ManyToManyField(
        Member, blank=True, related_name="individual_emails",
        verbose_name="Individuelle Empfänger"
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name="Geplante Sendezeit")
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Statistik
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_mass_emails"
    )
    sent_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_mass_emails"
    )

    class Meta:
        verbose_name = "Massen-E-Mail"
        verbose_name_plural = "Massen-E-Mails"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"


class EmailLog(models.Model):
    """Log für einzelne E-Mail-Versände"""
    STATUS_CHOICES = [
        ("pending", "Ausstehend"),
        ("sent", "Gesendet"),
        ("delivered", "Zugestellt"),
        ("opened", "Geöffnet"),
        ("failed", "Fehlgeschlagen"),
        ("bounced", "Bounced"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mass_email = models.ForeignKey(
        MassEmail, on_delete=models.CASCADE, related_name="email_logs"
    )
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="email_logs"
    )
    recipient_email = models.EmailField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    tracking_id = models.CharField(max_length=64, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "E-Mail-Log"
        verbose_name_plural = "E-Mail-Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mass_email", "status"]),
            models.Index(fields=["member", "created_at"]),
        ]

    def __str__(self):
        return f"{self.recipient_email} - {self.get_status_display()}"
