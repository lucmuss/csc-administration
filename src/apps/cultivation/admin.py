# cultivation/admin.py
from django.contrib import admin
from .models import GrowCycle, Plant, PlantLog, HarvestBatch


@admin.register(GrowCycle)
class GrowCycleAdmin(admin.ModelAdmin):
    list_display = [
        "name", "status", "start_date", "expected_harvest_date",
        "plant_count", "responsible_member", "created_at"
    ]
    list_filter = ["status", "start_date", "expected_harvest_date"]
    search_fields = ["name", "description", "location"]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "start_date"
    fieldsets = (
        (None, {
            "fields": ("id", "name", "description", "status")
        }),
        ("Zeitraum", {
            "fields": ("start_date", "expected_harvest_date", "actual_harvest_date", "completion_date")
        }),
        ("Zuordnung", {
            "fields": ("responsible_member", "location")
        }),
        ("Notizen", {
            "fields": ("notes", "compliance_notes")
        }),
        ("Meta", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = [
        "plant_number", "strain", "grow_cycle", "status",
        "planting_date", "expected_yield_grams", "actual_yield_grams"
    ]
    list_filter = ["status", "strain", "grow_cycle"]
    search_fields = ["plant_number", "qr_code_id", "notes"]
    readonly_fields = ["id", "qr_code_id", "created_at", "updated_at"]
    date_hierarchy = "planting_date"
    fieldsets = (
        (None, {
            "fields": ("id", "grow_cycle", "strain", "status")
        }),
        ("Identifikation", {
            "fields": ("plant_number", "qr_code_id")
        }),
        ("Zeitraum", {
            "fields": ("planting_date", "harvest_date")
        }),
        ("Ertrag", {
            "fields": ("expected_yield_grams", "actual_yield_grams")
        }),
        ("Notizen", {
            "fields": ("notes", "compliance_notes")
        }),
        ("Meta", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )


@admin.register(PlantLog)
class PlantLogAdmin(admin.ModelAdmin):
    list_display = ["plant", "log_type", "date", "performed_by", "created_at"]
    list_filter = ["log_type", "date", "performed_by"]
    search_fields = ["plant__plant_number", "notes", "products_used"]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "date"


@admin.register(HarvestBatch)
class HarvestBatchAdmin(admin.ModelAdmin):
    list_display = [
        "batch_number", "name", "harvest_date", "plant_count",
        "total_weight_fresh", "total_weight_dried", "quality_grade",
        "assigned_to_inventory"
    ]
    list_filter = ["quality_grade", "assigned_to_inventory", "harvest_date"]
    search_fields = ["batch_number", "name", "notes"]
    readonly_fields = ["id", "batch_number", "created_at", "updated_at"]
    date_hierarchy = "harvest_date"
    filter_horizontal = ["plants"]
    fieldsets = (
        (None, {
            "fields": ("id", "batch_number", "name", "harvest_date")
        }),
        ("Pflanzen", {
            "fields": ("plants",)
        }),
        ("Gewichte", {
            "fields": ("total_weight_fresh", "total_weight_dried", "quality_grade")
        }),
        ("Trocknung & Aushärtung", {
            "fields": (
                "drying_start_date", "drying_end_date",
                "curing_start_date", "curing_end_date"
            )
        }),
        ("Inventar", {
            "fields": ("assigned_to_inventory", "inventory_item")
        }),
        ("Notizen", {
            "fields": ("notes", "compliance_notes")
        }),
        ("Meta", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )
