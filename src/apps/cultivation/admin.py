from django.contrib import admin

from .models import BatchConnection, Cutting, GrowthLog, Harvest, MotherPlant, Plant


@admin.register(MotherPlant)
class MotherPlantAdmin(admin.ModelAdmin):
    list_display = ("id", "strain", "planted_date", "status", "genetics")
    list_filter = ("status", "strain")
    search_fields = ("strain__name", "genetics")


@admin.register(Cutting)
class CuttingAdmin(admin.ModelAdmin):
    list_display = ("id", "mother_plant", "planted_date", "rooting_date", "status")
    list_filter = ("status",)
    search_fields = ("mother_plant__strain__name",)


class GrowthLogInline(admin.TabularInline):
    model = GrowthLog
    extra = 0


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ("id", "cutting", "room", "planting_date", "growth_stage")
    list_filter = ("growth_stage", "room")
    search_fields = ("cutting__mother_plant__strain__name", "room")
    inlines = [GrowthLogInline]


@admin.register(Harvest)
class HarvestAdmin(admin.ModelAdmin):
    list_display = ("id", "plant", "harvest_date", "wet_weight", "dry_weight")
    search_fields = ("plant__cutting__mother_plant__strain__name",)


@admin.register(BatchConnection)
class BatchConnectionAdmin(admin.ModelAdmin):
    list_display = ("harvest", "batch", "created_at")
    search_fields = ("batch__code",)
