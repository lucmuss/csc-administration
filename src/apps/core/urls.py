from django.urls import path
from django.views.generic import RedirectView

from .views import dashboard, health, imprint, privacy, ready

app_name = "core"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("privacy/", privacy, name="privacy"),
    path("imprint/", imprint, name="imprint"),
    path("impressum/", RedirectView.as_view(pattern_name="core:imprint", permanent=False)),
    path("impressum.html", RedirectView.as_view(pattern_name="core:imprint", permanent=False)),
    path("health/", health, name="health"),
    path("ready/", ready, name="ready"),
]
