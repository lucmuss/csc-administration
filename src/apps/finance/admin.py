from django.contrib import admin

from .models import BalanceTopUp, BalanceTransaction, Invoice, Payment, Reminder, SepaMandate


@admin.register(SepaMandate)
class SepaMandateAdmin(admin.ModelAdmin):
    list_display = ("mandate_reference", "profile", "iban_masked", "is_active", "signed_at", "revoked_at")
    search_fields = ("mandate_reference", "profile__user__email", "iban")
    list_filter = ("is_active",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "profile", "amount", "due_date", "status", "reminder_level")
    search_fields = ("invoice_number", "profile__user__email")
    list_filter = ("status", "reminder_level")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice", "profile", "amount", "method", "status", "scheduled_for", "collected_at")
    search_fields = ("invoice__invoice_number", "profile__user__email", "sepa_batch_id")
    list_filter = ("method", "status")


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("invoice", "level", "fee_amount", "sent_at")
    search_fields = ("invoice__invoice_number", "invoice__profile__user__email")
    list_filter = ("level",)


@admin.register(BalanceTransaction)
class BalanceTransactionAdmin(admin.ModelAdmin):
    list_display = ("profile", "amount", "kind", "reference", "created_at")
    search_fields = ("profile__user__email", "reference", "note")
    list_filter = ("kind",)


@admin.register(BalanceTopUp)
class BalanceTopUpAdmin(admin.ModelAdmin):
    list_display = ("profile", "amount", "provider", "status", "checkout_session_id", "created_at")
    search_fields = ("profile__user__email", "checkout_session_id")
    list_filter = ("provider", "status")
