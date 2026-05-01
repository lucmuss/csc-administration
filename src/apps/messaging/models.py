# messaging/models.py
from django.db import models
from django.contrib.auth import get_user_model
from apps.members.models import Profile
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
    member = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="email_groups")
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ["group", "member"]
        verbose_name = "Gruppenmitglied"
        verbose_name_plural = "Gruppenmitglieder"


class EmailTemplate(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class MassEmail(models.Model):
    """Massen-E-Mail-Versand"""
    STATUS_DRAFT = "draft"
    STATUS_QUEUED = "queued"
    STATUS_SENDING = "sending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Entwurf"),
        (STATUS_QUEUED, "In Warteschlange"),
        (STATUS_SENDING, "Wird gesendet"),
        (STATUS_SENT, "Gesendet"),
        (STATUS_FAILED, "Fehlgeschlagen"),
        (STATUS_CANCELLED, "Abgebrochen"),
    ]

    RECIPIENT_ALL = "all"
    RECIPIENT_GROUP = "group"
    RECIPIENT_INDIVIDUAL = "individual"
    RECIPIENT_TYPE_CHOICES = [
        (RECIPIENT_ALL, "Alle Mitglieder"),
        (RECIPIENT_GROUP, "Bestimmte Gruppe"),
        (RECIPIENT_INDIVIDUAL, "Individuelle Auswahl"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=255, verbose_name="Betreff")
    content = models.TextField(verbose_name="Inhalt (Markdown)")
    content_html = models.TextField(blank=True, verbose_name="Inhalt (HTML)")
    
    # Empfänger
    recipient_type = models.CharField(
        max_length=20, choices=RECIPIENT_TYPE_CHOICES, default=RECIPIENT_ALL
    )
    recipient_group = models.ForeignKey(
        EmailGroup, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Empfängergruppe"
    )
    individual_recipients = models.ManyToManyField(
        Profile, blank=True, related_name="individual_emails",
        verbose_name="Individuelle Empfänger"
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
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
        Profile, on_delete=models.CASCADE, related_name="email_logs"
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


# ==================== SMS GATEWAY MODELS ====================

class SmsProviderConfig(models.Model):
    """Konfiguration für SMS-Provider"""
    PROVIDER_CHOICES = [
        ("twilio", "Twilio"),
        ("vonage", "Vonage"),
        ("custom", "Custom Webhook"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        verbose_name="Provider"
    )
    name = models.CharField(max_length=100, verbose_name="Bezeichnung")
    api_key = models.CharField(max_length=255, verbose_name="API Key")
    api_secret = models.CharField(max_length=255, blank=True, verbose_name="API Secret")
    sender_number = models.CharField(max_length=20, verbose_name="Absendernummer")
    webhook_url = models.URLField(blank=True, verbose_name="Webhook URL")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    cost_per_sms = models.DecimalField(
        max_digits=6, decimal_places=4, default=0.0000,
        verbose_name="Kosten pro SMS (€)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_sms_providers"
    )

    class Meta:
        verbose_name = "SMS-Provider"
        verbose_name_plural = "SMS-Provider"
        ordering = ["-is_active", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_provider_display()})"


class SmsMessage(models.Model):
    """SMS-Nachricht"""
    STATUS_CHOICES = [
        ("draft", "Entwurf"),
        ("queued", "In Warteschlange"),
        ("sending", "Wird gesendet"),
        ("sent", "Gesendet"),
        ("delivered", "Zugestellt"),
        ("failed", "Fehlgeschlagen"),
    ]

    RECIPIENT_TYPE_CHOICES = [
        ("individual", "Einzelner Empfänger"),
        ("group", "Gruppe"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Empfänger
    recipient_type = models.CharField(
        max_length=20, choices=RECIPIENT_TYPE_CHOICES, default="individual"
    )
    recipient_phone = models.CharField(max_length=20, blank=True, verbose_name="Empfängernummer")
    recipient_member = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sms_messages", verbose_name="Empfänger (Mitglied)"
    )
    recipient_group = models.ForeignKey(
        EmailGroup, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sms_messages", verbose_name="Empfängergruppe"
    )
    
    # Inhalt
    content = models.TextField(max_length=1600, verbose_name="Nachricht")
    template_used = models.ForeignKey(
        "SmsTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="messages", verbose_name="Verwendetes Template"
    )
    
    # Provider & Status
    provider = models.ForeignKey(
        SmsProviderConfig, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="messages", verbose_name="SMS-Provider"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    external_id = models.CharField(max_length=255, blank=True, verbose_name="Externe ID")
    error_message = models.TextField(blank=True, verbose_name="Fehlermeldung")
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Gesendet am")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Zugestellt am")
    cost = models.DecimalField(max_digits=6, decimal_places=4, default=0.0000, verbose_name="Kosten (€)")
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_sms_messages"
    )
    sent_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_sms_messages"
    )

    class Meta:
        verbose_name = "SMS-Nachricht"
        verbose_name_plural = "SMS-Nachrichten"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["recipient_member", "created_at"]),
        ]

    def __str__(self):
        if self.recipient_member:
            return f"SMS an {self.recipient_member} ({self.get_status_display()})"
        return f"SMS an {self.recipient_phone} ({self.get_status_display()})"

    @property
    def character_count(self):
        return len(self.content)

    @property
    def sms_count(self):
        """Berechnet die Anzahl der SMS (160 Zeichen pro SMS)"""
        chars = self.character_count
        if chars <= 160:
            return 1
        return (chars + 153 - 1) // 153  # 153 Zeichen bei verketteten SMS


class SmsTemplate(models.Model):
    """Vorlagen für SMS-Nachrichten"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Name")
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    content = models.TextField(max_length=1600, verbose_name="Vorlage")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_sms_templates"
    )

    class Meta:
        verbose_name = "SMS-Vorlage"
        verbose_name_plural = "SMS-Vorlagen"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def render(self, context):
        """Rendert die Vorlage mit den gegebenen Variablen"""
        from django.template import Template, Context as DjangoContext
        template = Template(self.content)
        return template.render(DjangoContext(context))


class SmsCostLog(models.Model):
    """Log für SMS-Kosten"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    month = models.CharField(max_length=7, verbose_name="Monat (YYYY-MM)")
    total_messages = models.IntegerField(default=0, verbose_name="Gesamtanzahl")
    total_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0.0000, verbose_name="Gesamtkosten (€)")
    provider_breakdown = models.JSONField(default=dict, verbose_name="Provider-Details")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SMS-Kosten-Log"
        verbose_name_plural = "SMS-Kosten-Logs"
        ordering = ["-month"]
        unique_together = ["month"]

    def __str__(self):
        return f"SMS-Kosten {self.month}: {self.total_cost}€"
