from django.urls import path

from .views import dashboard, feature_audit_view, health, imprint, privacy, ready

app_name = "core"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("privacy/", privacy, name="privacy"),
    path("imprint/", imprint, name="imprint"),
    path("health/", health, name="health"),
    path("ready/", ready, name="ready"),
    path("board/features/", feature_audit_view, name="feature_audit"),
]
