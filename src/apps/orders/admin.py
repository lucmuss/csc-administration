from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("strain", "quantity_grams", "unit_price", "total_price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "member", "status", "total", "total_grams", "reserved_until", "created_at")
    list_filter = ("status",)
    search_fields = ("member__email",)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "strain", "quantity_grams", "total_price")
