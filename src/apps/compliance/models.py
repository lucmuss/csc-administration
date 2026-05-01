from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class _LegacyKeywordManager(models.Manager):
    def _normalize(self, kwargs: dict, *, fill_defaults: bool = False):
        data = dict(kwargs)
        model_field_names = {field.name for field in self.model._meta.get_fields()}
        if "member" in data and "profile" not in data:
            data["profile"] = data.pop("member")
        if "description" in data and "notes" not in data:
            data["notes"] = data.pop("description")
        data.pop("activity_type", None)
        data.pop("detected_at", None)
        acknowledged = data.pop("acknowledged", None)
        if acknowledged is not None and "acknowledged_at" not in data:
            data["acknowledged_at"] = None
        data.pop("info_type", None)
        profile = data.get("profile")
        if fill_defaults and "month_key" in model_field_names and "month_key" not in data and profile is not None:
            data["month_key"] = getattr(profile, "monthly_counter_key", "") or timezone.localdate().strftime("%Y-%m")
        if fill_defaults and "consumed_grams" in model_field_names and "consumed_grams" not in data and profile is not None:
            data["consumed_grams"] = getattr(profile, "monthly_used", Decimal("0.00")) or Decimal("0.00")
        if fill_defaults and "consumed_grams" in model_field_names and "consumed_grams" not in data:
            data["consumed_grams"] = Decimal("0.00")
        return data

    def create(self, **kwargs):
        return super().create(**self._normalize(kwargs, fill_defaults=True))

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self._normalize(kwargs))

    def get(self, *args, **kwargs):
        return super().get(*args, **self._normalize(kwargs))

    def update_or_create(self, defaults=None, **kwargs):
        normalized_defaults = self._normalize(defaults or {}, fill_defaults=True)
        return super().update_or_create(defaults=normalized_defaults, **self._normalize(kwargs, fill_defaults=True))


class ComplianceReport(models.Model):
    year = models.PositiveIntegerField(unique=True)
    generated_at = models.DateTimeField(auto_now=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_compliance_reports",
    )

    total_orders = models.PositiveIntegerField(default=0)
    total_members = models.PositiveIntegerField(default=0)
    total_grams = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    suspicious_cases = models.PositiveIntegerField(default=0)

    report_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-year"]

    def __str__(self):
        return f"Compliance-Bericht {self.year} · Mitglieder {self.total_members} · Abgaben {self.total_orders}"


class SuspiciousActivity(models.Model):
    TYPE_EXCESS_CONSUMPTION = "excess_consumption"

    profile = models.ForeignKey("members.Profile", on_delete=models.CASCADE, related_name="suspicious_activities")
    month_key = models.CharField(max_length=7, db_index=True)
    consumed_grams = models.DecimalField(max_digits=8, decimal_places=2)
    threshold_grams = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("50.00"))
    detected_at = models.DateTimeField(auto_now=True)

    is_reported = models.BooleanField(default=False)
    reported_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    objects = _LegacyKeywordManager()

    def __init__(self, *args, **kwargs):
        if "member" in kwargs and "profile" not in kwargs:
            kwargs["profile"] = kwargs.pop("member")
        if "description" in kwargs and "notes" not in kwargs:
            kwargs["notes"] = kwargs.pop("description")
        kwargs.pop("activity_type", None)
        kwargs.pop("detected_at", None)
        super().__init__(*args, **kwargs)

    class Meta:
        ordering = ["-detected_at"]
        verbose_name = "Verdaechtige Aktivitaet"
        verbose_name_plural = "Verdaechtige Aktivitaeten"
        constraints = [
            models.UniqueConstraint(fields=["profile", "month_key"], name="unique_profile_month_suspicious_activity")
        ]

    def __str__(self):
        return f"Verdacht {self.profile} {self.month_key}"


class PreventionInfo(models.Model):
    TYPE_FIRST_DISPENSE = "first_dispense"

    profile = models.OneToOneField("members.Profile", on_delete=models.CASCADE, related_name="prevention_info")
    first_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prevention_infos",
    )
    provided_at = models.DateTimeField(auto_now_add=True)
    info_version = models.CharField(max_length=32, default="CanG-2024")
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    objects = _LegacyKeywordManager()

    def __init__(self, *args, **kwargs):
        if "member" in kwargs and "profile" not in kwargs:
            kwargs["profile"] = kwargs.pop("member")
        kwargs.pop("info_type", None)
        acknowledged = kwargs.pop("acknowledged", None)
        if acknowledged is not None and "acknowledged_at" not in kwargs:
            kwargs["acknowledged_at"] = None
        super().__init__(*args, **kwargs)

    class Meta:
        ordering = ["-provided_at"]

    def __str__(self):
        return f"Praeventionsinfo {self.profile}"

    @property
    def acknowledged(self) -> bool:
        return bool(self.acknowledged_at)
