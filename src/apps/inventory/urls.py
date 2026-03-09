from django.urls import path
from django.views.generic import RedirectView

from .views import discrepancy_report, inventory_count_form, location_list, strain_list

app_name = "inventory"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="inventory:strain_list", permanent=False)),
    path("strains/", strain_list, name="strain_list"),
    path("locations/", location_list, name="location_list"),
    path("count/", inventory_count_form, name="inventory_count_form"),
    path("discrepancies/", discrepancy_report, name="discrepancy_report"),
]
