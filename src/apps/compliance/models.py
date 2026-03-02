from decimal import Decimal

from django.conf import settings
from django.db import models


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
        return f"Compliance-Bericht {self.year}"


class SuspiciousActivity(models.Model):
    profile = models.ForeignKey("members.Profile", on_delete=models.CASCADE, related_name="suspicious_activities")
    month_key = models.CharField(max_length=7, db_index=True)
    consumed_grams = models.DecimalField(max_digits=8, decimal_places=2)
    threshold_grams = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("50.00"))
    detected_at = models.DateTimeField(auto_now=True)

    is_reported = models.BooleanField(default=False)
    reported_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-detected_at"]
        constraints = [
            models.UniqueConstraint(fields=["profile", "month_key"], name="unique_profile_month_suspicious_activity")
        ]

    def __str__(self):
        return f"Verdacht {self.profile} {self.month_key}"


class PreventionInfo(models.Model):
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

    class Meta:
        ordering = ["-provided_at"]

    def __str__(self):
        return f"Praeventionsinfo {self.profile}"
