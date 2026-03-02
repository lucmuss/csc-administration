from django.contrib import admin

from .models import Batch, InventoryCount, InventoryItem, InventoryLocation, Strain


@admin.register(Strain)
class StrainAdmin(admin.ModelAdmin):
    list_display = ("name", "quality_grade", "thc", "cbd", "price", "stock", "is_active")
    search_fields = ("name",)
    list_filter = ("quality_grade", "is_active")


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
