# cultivation/urls.py
from django.urls import path
from . import views

app_name = "cultivation"

urlpatterns = [
    # Dashboard
    path("", views.cultivation_dashboard, name="dashboard"),
    
    # Grow Cycles
    path("cycles/", views.grow_cycle_list, name="grow_cycle_list"),
    path("cycles/create/", views.grow_cycle_create, name="grow_cycle_create"),
    path("cycles/<uuid:pk>/", views.grow_cycle_detail, name="grow_cycle_detail"),
    path("cycles/<uuid:pk>/edit/", views.grow_cycle_edit, name="grow_cycle_edit"),
    path("cycles/<uuid:pk>/delete/", views.grow_cycle_delete, name="grow_cycle_delete"),
    path("cycles/<uuid:pk>/update-status/", views.grow_cycle_update_status, name="grow_cycle_update_status"),
    
    # Plants
    path("plants/", views.plant_list, name="plant_list"),
    path("plants/create/", views.plant_create, name="plant_create"),
    path("plants/<uuid:pk>/", views.plant_detail, name="plant_detail"),
    path("plants/<uuid:pk>/edit/", views.plant_edit, name="plant_edit"),
    path("plants/<uuid:pk>/delete/", views.plant_delete, name="plant_delete"),
    path("plants/<uuid:pk>/update-status/", views.plant_update_status, name="plant_update_status"),
    path("plants/<uuid:pk>/qr/", views.plant_qr_code, name="plant_qr_code"),
    
    # Plant Logs
    path("plants/<uuid:plant_pk>/logs/create/", views.plant_log_create, name="plant_log_create"),
    path("plants/<uuid:plant_pk>/logs/", views.plant_log_list, name="plant_log_list"),
    
    # Harvest Batches
    path("harvest/", views.harvest_list, name="harvest_list"),
    path("harvest/create/", views.harvest_create, name="harvest_create"),
    path("harvest/<uuid:pk>/", views.harvest_detail, name="harvest_detail"),
    path("harvest/<uuid:pk>/edit/", views.harvest_edit, name="harvest_edit"),
    path("harvest/<uuid:pk>/delete/", views.harvest_delete, name="harvest_delete"),
    path("harvest/<uuid:pk>/assign-inventory/", views.harvest_assign_to_inventory, name="harvest_assign_inventory"),
    
    # API
    path("api/plants/stats/", views.api_plant_stats, name="api_plant_stats"),
    path("api/cycles/<uuid:pk>/stats/", views.api_grow_cycle_stats, name="api_grow_cycle_stats"),
]
