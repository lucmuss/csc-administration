from django.contrib import admin
from django.utils.html import format_html

from .models import Batch, InventoryCount, InventoryItem, InventoryLocation, Strain


@admin.register(Strain)
class StrainAdmin(admin.ModelAdmin):
    list_display = ("image_preview", "name", "product_type", "quality_grade", "thc", "cbd", "price", "stock", "is_active")
    list_editable = ("product_type", "price", "stock", "is_active")
    search_fields = ("name",)
    list_filter = ("product_type", "quality_grade", "is_active")
    readonly_fields = ("image_preview",)
    fields = ("name", "product_type", "image", "image_preview", "thc", "cbd", "price", "stock", "quality_grade", "is_active")

    def image_preview(self, obj):
        if not obj.image:
            return "Kein Bild"
        return format_html(
            '<img src="{}" alt="{}" style="width: 72px; height: 72px; object-fit: cover; border-radius: 12px;" />',
            obj.image.url,
            obj.name,
        )

    image_preview.short_description = "Shop-Bild"


@admin.register(InventoryLocation)
class InventoryLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "capacity")
    list_filter = ("type",)
    search_fields = ("name",)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("strain", "location", "quantity", "last_counted")
    list_filter = ("location", "strain")
    search_fields = ("strain__name", "location__name")


@admin.register(InventoryCount)
class InventoryCountAdmin(admin.ModelAdmin):
    list_display = ("date", "items_counted")
    readonly_fields = ("items_counted", "discrepancies")


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("code", "strain", "quantity", "harvested_at", "is_active", "created_at")
    list_filter = ("is_active", "strain")
    search_fields = ("code", "strain__name")
