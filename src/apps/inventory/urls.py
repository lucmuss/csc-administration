from django.urls import path
from django.views.generic import RedirectView

from .views import (
    discrepancy_report,
    inventory_count_form,
    location_create,
    location_delete,
    location_edit,
    location_list,
    strain_create,
    strain_detail,
    strain_edit,
    strain_list,
)

app_name = "inventory"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="inventory:strain_list", permanent=False)),
    path("strains/", strain_list, name="strain_list"),
    path("strains/new/", strain_create, name="strain_create"),
    path("strains/<int:pk>/", strain_detail, name="strain_detail"),
    path("strains/<int:pk>/edit/", strain_edit, name="strain_edit"),
    path("locations/", location_list, name="location_list"),
    path("locations/new/", location_create, name="location_create"),
    path("locations/<int:pk>/edit/", location_edit, name="location_edit"),
    path("locations/<int:pk>/delete/", location_delete, name="location_delete"),
    path("count/", inventory_count_form, name="inventory_count_form"),
    path("discrepancies/", discrepancy_report, name="discrepancy_report"),
]
