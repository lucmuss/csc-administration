# messaging/admin.py
from django.contrib import admin
from .models import (
    EmailGroup, EmailGroupMember, MassEmail, EmailLog,
    SmsProviderConfig, SmsMessage, SmsTemplate, SmsCostLog
)


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
    search_fields = ["member__user__first_name", "member__user__last_name", "member__user__email"]


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
    search_fields = ["recipient_email", "member__user__first_name", "member__user__last_name"]
    readonly_fields = ["id", "tracking_id", "created_at", "updated_at"]


# ==================== SMS ADMIN ====================

@admin.register(SmsProviderConfig)
class SmsProviderConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "provider", "sender_number", "is_active", "cost_per_sms", "updated_at"]
    list_filter = ["provider", "is_active"]
    search_fields = ["name", "sender_number"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        (None, {
            "fields": ("name", "provider", "is_active")
        }),
        ("API-Konfiguration", {
            "fields": ("api_key", "api_secret", "sender_number", "webhook_url")
        }),
        ("Kosten", {
            "fields": ("cost_per_sms",)
        }),
        ("Meta", {
            "fields": ("id", "created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )


@admin.register(SmsMessage)
class SmsMessageAdmin(admin.ModelAdmin):
    list_display = [
        "recipient_display", "character_count", "sms_count", "status",
        "provider", "cost", "sent_at", "created_at"
    ]
    list_filter = ["status", "provider", "recipient_type", "created_at"]
    search_fields = ["recipient_phone", "content", "recipient_member__user__first_name", "recipient_member__user__last_name"]
    readonly_fields = [
        "id", "character_count", "sms_count", "external_id",
        "sent_at", "delivered_at", "created_at", "updated_at"
    ]
    date_hierarchy = "created_at"
    fieldsets = (
        (None, {
            "fields": ("id", "status", "recipient_type")
        }),
        ("Empfänger", {
            "fields": ("recipient_member", "recipient_group", "recipient_phone")
        }),
        ("Inhalt", {
            "fields": ("content", "template_used", "character_count", "sms_count")
        }),
        ("Provider & Tracking", {
            "fields": ("provider", "external_id", "cost", "sent_at", "delivered_at", "error_message")
        }),
        ("Meta", {
            "fields": ("created_at", "updated_at", "created_by", "sent_by"),
            "classes": ("collapse",)
        }),
    )

    def recipient_display(self, obj):
        if obj.recipient_member:
            return f"{obj.recipient_member}"
        return obj.recipient_phone or "-"
    recipient_display.short_description = "Empfänger"


@admin.register(SmsTemplate)
class SmsTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "character_count", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "content"]
    readonly_fields = ["id", "created_at", "updated_at", "character_count"]
    
    def character_count(self, obj):
        return len(obj.content)
    character_count.short_description = "Zeichen"


@admin.register(SmsCostLog)
class SmsCostLogAdmin(admin.ModelAdmin):
    list_display = ["month", "total_messages", "total_cost", "updated_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    search_fields = ["month"]
