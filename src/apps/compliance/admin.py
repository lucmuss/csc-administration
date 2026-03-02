from django.contrib import admin

from .models import ComplianceReport, PreventionInfo, SuspiciousActivity


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ("year", "total_orders", "total_members", "total_grams", "suspicious_cases", "generated_at")
    search_fields = ("year",)


@admin.register(SuspiciousActivity)
class SuspiciousActivityAdmin(admin.ModelAdmin):
    list_display = ("profile", "month_key", "consumed_grams", "threshold_grams", "is_reported", "detected_at")
    list_filter = ("is_reported", "month_key")
    search_fields = ("profile__user__email", "profile__member_number")


@admin.register(PreventionInfo)
class PreventionInfoAdmin(admin.ModelAdmin):
    list_display = ("profile", "first_order", "info_version", "provided_at", "acknowledged_at")
    search_fields = ("profile__user__email", "profile__member_number")
