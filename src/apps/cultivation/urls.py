from django.urls import path

from .views import cutting_list, dashboard, harvest_form, mother_plant_list, plant_detail

app_name = "cultivation"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("mothers/", mother_plant_list, name="mother_plant_list"),
    path("cuttings/", cutting_list, name="cutting_list"),
    path("plants/<int:plant_id>/", plant_detail, name="plant_detail"),
    path("plants/<int:plant_id>/harvest/", harvest_form, name="harvest_form"),
]
