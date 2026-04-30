from django.contrib import admin

from .models import Profile, VerificationSubmission


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "member_number",
        "user",
        "status",
        "is_verified",
        "is_locked_for_orders",
        "balance",
        "daily_used",
        "monthly_used",
        "work_hours_done",
        "last_activity",
    )
    search_fields = ("user__email", "member_number")
    list_filter = ("status", "is_verified", "is_locked_for_orders")


@admin.register(VerificationSubmission)
class VerificationSubmissionAdmin(admin.ModelAdmin):
    list_display = ("profile", "status", "submitted_at", "approved_at", "approved_by")
    search_fields = ("profile__user__email", "profile__member_number")
    list_filter = ("status",)
