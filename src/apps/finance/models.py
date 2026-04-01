from django.conf import settings
from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.members.models import Profile


class SepaMandate(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="sepa_mandates")
    iban = models.CharField(max_length=34)
    bic = models.CharField(max_length=11)
    account_holder = models.CharField(max_length=255)
    mandate_reference = models.CharField(max_length=64, unique=True)
    signed_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.mandate_reference} ({self.profile})"

    @property
    def iban_masked(self) -> str:
        tail = self.iban[-4:] if len(self.iban) >= 4 else self.iban
        return f"•••• •••• •••• {tail}"


class Invoice(models.Model):
    STATUS_OPEN = "open"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Offen"),
        (STATUS_PAID, "Bezahlt"),
        (STATUS_CANCELLED, "Storniert"),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="invoices")
    order = models.OneToOneField("orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="invoice")
    invoice_number = models.CharField(max_length=32, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    reminder_level = models.PositiveSmallIntegerField(default=0)
    blocked_member = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.invoice_number

    def next_reminder_date(self):
        offsets = {
            0: timedelta(days=7),
            1: timedelta(days=14),
            2: timedelta(days=21),
            3: timedelta(days=28),
        }
        offset = offsets.get(self.reminder_level)
        if not offset:
            return None
        return self.due_date + offset


class Payment(models.Model):
    METHOD_BALANCE = "balance"
    METHOD_SEPA = "sepa"
    METHOD_CHOICES = [
        (METHOD_BALANCE, "Guthaben"),
        (METHOD_SEPA, "SEPA"),
    ]

    STATUS_PENDING = "pending"
    STATUS_PRNOTIFIED = "pre_notified"
    STATUS_COLLECTED = "collected"
    STATUS_RETURNED = "returned"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Ausstehend"),
        (STATUS_PRNOTIFIED, "Vorabankuendigung gesendet"),
        (STATUS_COLLECTED, "Eingezogen"),
        (STATUS_RETURNED, "Ruecklaeufer"),
        (STATUS_FAILED, "Fehlgeschlagen"),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="payments")
    mandate = models.ForeignKey(SepaMandate, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=16, choices=METHOD_CHOICES, default=METHOD_SEPA)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDING)
    scheduled_for = models.DateField(default=timezone.localdate)
    prenotified_at = models.DateTimeField(null=True, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    sepa_batch_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.id} {self.amount} {self.get_status_display()}"


class Reminder(models.Model):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_CHOICES = [
        (LEVEL_1, "Erinnerung"),
        (LEVEL_2, "1. Mahnung"),
        (LEVEL_3, "2. Mahnung"),
        (LEVEL_4, "3. Mahnung"),
    ]

    FEE_BY_LEVEL = {
        LEVEL_1: Decimal("0.00"),
        LEVEL_2: Decimal("5.00"),
        LEVEL_3: Decimal("10.00"),
        LEVEL_4: Decimal("15.00"),
    }

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="reminders")
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES)
    fee_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    sent_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-sent_at"]
        unique_together = ("invoice", "level")

    def __str__(self):
        return f"{self.invoice.invoice_number} / L{self.level}"


class BalanceTransaction(models.Model):
    KIND_MEMBERSHIP_FEE = "membership_fee"
    KIND_TOPUP = "topup"
    KIND_MANUAL_ADJUSTMENT = "manual_adjustment"
    KIND_ORDER_CHARGE = "order_charge"
    KIND_ORDER_REFUND = "order_refund"
    KIND_CHOICES = [
        (KIND_MEMBERSHIP_FEE, "Mitgliedsbeitrag"),
        (KIND_TOPUP, "Aufladung"),
        (KIND_MANUAL_ADJUSTMENT, "Manuelle Anpassung"),
        (KIND_ORDER_CHARGE, "Bestellung belastet"),
        (KIND_ORDER_REFUND, "Bestellung erstattet"),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="balance_transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    note = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=128, blank=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_balance_transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.profile} {self.amount} {self.kind}"


class BalanceTopUp(models.Model):
    PROVIDER_STRIPE = "stripe"
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_EXPIRED = "expired"

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="balance_topups")
    provider = models.CharField(max_length=16, default=PROVIDER_STRIPE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="eur")
    status = models.CharField(
        max_length=16,
        choices=[
            (STATUS_PENDING, "Ausstehend"),
            (STATUS_COMPLETED, "Abgeschlossen"),
            (STATUS_FAILED, "Fehlgeschlagen"),
            (STATUS_EXPIRED, "Abgelaufen"),
        ],
        default=STATUS_PENDING,
    )
    checkout_session_id = models.CharField(max_length=255, unique=True, blank=True)
    checkout_url = models.URLField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.profile} {self.amount} {self.provider} {self.status}"


class UploadedInvoice(models.Model):
    DIRECTION_INCOMING = "incoming"
    DIRECTION_OUTGOING = "outgoing"
    DIRECTION_CHOICES = [
        (DIRECTION_INCOMING, "Eingangsrechnung"),
        (DIRECTION_OUTGOING, "Ausgangsrechnung"),
    ]

    EXTRACTION_PENDING = "pending"
    EXTRACTION_SUCCESS = "success"
    EXTRACTION_FAILED = "failed"
    EXTRACTION_CHOICES = [
        (EXTRACTION_PENDING, "Ausstehend"),
        (EXTRACTION_SUCCESS, "Erkannt"),
        (EXTRACTION_FAILED, "Pruefen"),
    ]

    PAYMENT_OPEN = "open"
    PAYMENT_PAID = "paid"
    PAYMENT_CANCELLED = "cancelled"
    PAYMENT_CHOICES = [
        (PAYMENT_OPEN, "Offen"),
        (PAYMENT_PAID, "Bezahlt"),
        (PAYMENT_CANCELLED, "Storniert"),
    ]

    title = models.CharField(max_length=180, blank=True)
    direction = models.CharField(max_length=16, choices=DIRECTION_CHOICES, default=DIRECTION_INCOMING)
    document = models.FileField(upload_to="finance/invoices/")
    invoice_number = models.CharField(max_length=120, blank=True)
    vendor_name = models.CharField(max_length=180, blank=True)
    customer_name = models.CharField(max_length=180, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    amount_net = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    amount_tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    amount_gross = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=8, default="EUR")
    payment_status = models.CharField(max_length=16, choices=PAYMENT_CHOICES, default=PAYMENT_OPEN)
    paid_at = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_uploaded_invoices",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_uploaded_invoices",
    )
    notes = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    ai_payload = models.JSONField(default=dict, blank=True)
    extraction_status = models.CharField(max_length=16, choices=EXTRACTION_CHOICES, default=EXTRACTION_PENDING)
    extraction_error = models.CharField(max_length=255, blank=True)
    extracted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date", "-created_at", "-id"]

    def __str__(self):
        return self.title
