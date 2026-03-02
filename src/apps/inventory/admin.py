from django.contrib import admin

from .models import Strain


@admin.register(Strain)
class StrainAdmin(admin.ModelAdmin):
    list_display = ("name", "thc", "cbd", "price", "stock", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)
