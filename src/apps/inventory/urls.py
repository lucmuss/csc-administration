from django.urls import path
from django.views.generic import RedirectView

from .views import (
    batch_create,
    batch_delete,
    batch_detail,
    dashboard,
    discrepancy_report,
    inventory_count_form,
    location_create,
    location_delete,
    location_edit,
    location_list,
    strain_create,
    strain_delete,
    strain_detail,
    strain_edit,
    strain_list,
    strain_update,
)

app_name = "inventory"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="inventory:strain_list", permanent=False)),
    path("strains/", strain_list, name="strain_list"),
    path("strains/new/", strain_create, name="strain_create"),
    path("strains/<int:pk>/", strain_detail, name="strain_detail"),
    path("strains/<int:pk>/edit/", strain_edit, name="strain_edit"),
    path("strains/<int:pk>/update/", strain_update, name="strain_update"),
    path("strains/<int:pk>/delete/", strain_delete, name="strain_delete"),
    path("dashboard/", dashboard, name="dashboard"),
    path("batches/new/", batch_create, name="batch_create"),
    path("batches/<int:pk>/", batch_detail, name="batch_detail"),
    path("batches/<int:pk>/delete/", batch_delete, name="batch_delete"),
    path("locations/", location_list, name="location_list"),
    path("locations/new/", location_create, name="location_create"),
    path("locations/<int:pk>/edit/", location_edit, name="location_edit"),
    path("locations/<int:pk>/delete/", location_delete, name="location_delete"),
    path("count/", inventory_count_form, name="inventory_count_form"),
    path("discrepancies/", discrepancy_report, name="discrepancy_report"),
]
