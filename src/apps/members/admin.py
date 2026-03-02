from django.contrib import admin

from .models import Profile


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
    )
    search_fields = ("user__email", "member_number")
    list_filter = ("status", "is_verified", "is_locked_for_orders")
