from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone


class Profile(models.Model):
    STATUS_PENDING = "pending"
    STATUS_VERIFIED = "verified"
    STATUS_ACTIVE = "active"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Ausstehend"),
        (STATUS_VERIFIED, "Verifiziert"),
        (STATUS_ACTIVE, "Aktiv"),
        (STATUS_REJECTED, "Abgelehnt"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    birth_date = models.DateField()
    member_number = models.BigIntegerField(unique=True, null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    is_verified = models.BooleanField(default=False)
    desired_join_date = models.DateField(null=True, blank=True)
    street_address = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    bank_name = models.CharField(max_length=150, blank=True)
    account_holder_name = models.CharField(max_length=255, blank=True)
    privacy_accepted = models.BooleanField(default=False)
    direct_debit_accepted = models.BooleanField(default=False)
    no_other_csc_membership = models.BooleanField(default=False)
    german_residence_confirmed = models.BooleanField(default=False)
    minimum_age_confirmed = models.BooleanField(default=False)
    id_document_confirmed = models.BooleanField(default=False)
    important_newsletter_opt_in = models.BooleanField(default=False)
    optional_newsletter_opt_in = models.BooleanField(default=False)
    instagram_opt_in = models.BooleanField(default=False)
    telegram_opt_in = models.BooleanField(default=False)
    application_notes = models.TextField(blank=True)
    registration_completed_at = models.DateTimeField(null=True, blank=True)

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    sepa_mandate = models.OneToOneField(
        "finance.SepaMandate",
        on_delete=models.SET_NULL,
        related_name="active_for_profile",
        null=True,
        blank=True,
    )
    is_locked_for_orders = models.BooleanField(default=False)

    daily_used = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    monthly_used = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    daily_counter_date = models.DateField(default=date.today)
    monthly_counter_key = models.CharField(max_length=7, default="1970-01")
    last_activity = models.DateTimeField(null=True, blank=True)
    work_hours_done = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["member_number", "id"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(daily_used__lte=25),
                name="daily_limit_25g_check"
            ),
            models.CheckConstraint(
                check=models.Q(monthly_used__lte=50),
                name="monthly_limit_50g_check"
            ),
        ]
        indexes = [
            models.Index(fields=["status", "is_verified"]),
            models.Index(fields=["daily_counter_date"]),
            models.Index(fields=["monthly_counter_key"]),
        ]

    def __str__(self):
        return f"{self.user.email} ({self.member_number or 'neu'})"

    @staticmethod
    def _month_key(day: date) -> str:
        return day.strftime("%Y-%m")

    def clean(self):
        minimum_age = getattr(settings, "MEMBER_MINIMUM_AGE", 21)
        if self.birth_date and self.age < minimum_age:
            raise ValidationError(f"Mitglied muss mindestens {minimum_age} Jahre alt sein.")

    @property
    def age(self) -> int:
        today = date.today()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years

    def reset_limits_if_due(self, today: date | None = None) -> None:
        today = today or date.today()
        changed = False

        if self.daily_counter_date != today:
            self.daily_used = Decimal("0.00")
            self.daily_counter_date = today
            changed = True

        month_key = self._month_key(today)
        if self.monthly_counter_key != month_key:
            self.monthly_used = Decimal("0.00")
            self.monthly_counter_key = month_key
            changed = True

        if changed:
            self.save(update_fields=["daily_used", "monthly_used", "daily_counter_date", "monthly_counter_key", "updated_at"])

    def can_consume(self, grams: Decimal) -> tuple[bool, str]:
        self.reset_limits_if_due()
        if self.daily_used + grams > Decimal("25.00"):
            return False, "Tageslimit von 25g ueberschritten"
        if self.monthly_used + grams > Decimal("50.00"):
            return False, "Monatslimit von 50g ueberschritten"
        return True, "OK"

    def consume(self, grams: Decimal) -> None:
        self.reset_limits_if_due()
        self.daily_used += grams
        self.monthly_used += grams
        self.save(update_fields=["daily_used", "monthly_used", "updated_at"])

    def allocate_member_number(self) -> None:
        if self.member_number:
            return
        with transaction.atomic():
            max_number = Profile.objects.select_for_update().aggregate(Max("member_number"))["member_number__max"]
            self.member_number = (max_number + 1) if max_number else 100000
            self.save(update_fields=["member_number", "updated_at"])

    @property
    def onboarding_complete(self) -> bool:
        has_active_mandate = bool(
            self.sepa_mandate_id
            or self.sepa_mandates.filter(is_active=True).exists()
        )
        return bool(
            self.desired_join_date
            and self.street_address
            and self.postal_code
            and self.city
            and self.phone
            and self.bank_name
            and self.account_holder_name
            and self.privacy_accepted
            and self.direct_debit_accepted
            and self.no_other_csc_membership
            and self.german_residence_confirmed
            and self.minimum_age_confirmed
            and self.id_document_confirmed
            and self.important_newsletter_opt_in
            and has_active_mandate
            and self.registration_completed_at
        )

    def mark_registration_completed(self) -> None:
        self.registration_completed_at = timezone.now()
        self.save(update_fields=["registration_completed_at", "updated_at"])
