# messaging/admin.py
from django.contrib import admin
from .models import EmailGroup, EmailGroupMember, MassEmail, EmailLog


@admin.register(EmailGroup)
class EmailGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "member_count", "is_active", "created_at", "created_by"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(EmailGroupMember)
class EmailGroupMemberAdmin(admin.ModelAdmin):
    list_display = ["group", "member", "added_at"]
    list_filter = ["group", "added_at"]
    search_fields = ["member__first_name", "member__last_name", "member__email"]


@admin.register(MassEmail)
class MassEmailAdmin(admin.ModelAdmin):
    list_display = ["subject", "recipient_type", "status", "total_recipients", "sent_count", "created_at"]
    list_filter = ["status", "recipient_type", "created_at"]
    search_fields = ["subject", "content"]
    readonly_fields = ["id", "created_at", "updated_at", "sent_at"]
    date_hierarchy = "created_at"


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ["recipient_email", "mass_email", "status", "sent_at", "opened_at"]
    list_filter = ["status", "sent_at", "opened_at"]
    search_fields = ["recipient_email", "member__first_name", "member__last_name"]
    readonly_fields = ["id", "tracking_id", "created_at", "updated_at"]
