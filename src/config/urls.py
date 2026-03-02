from django.contrib import admin
from django.views.generic import TemplateView
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "manifest.json",
        TemplateView.as_view(
            template_name="manifest.json", content_type="application/manifest+json"
        ),
        name="manifest",
    ),
    path(
        "offline.js",
        TemplateView.as_view(
            template_name="offline.js", content_type="application/javascript"
        ),
        name="offline_js",
    ),
    path("offline/", TemplateView.as_view(template_name="offline.html"), name="offline"),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("members/", include("apps.members.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("orders/", include("apps.orders.urls")),
    path("compliance/", include("apps.compliance.urls")),
    path("finance/", include("apps.finance.urls")),
    path("participation/", include("apps.participation.urls")),
]
