from django.urls import path

from .views import strain_list

app_name = "inventory"

urlpatterns = [
    path("strains/", strain_list, name="strain_list"),
]
