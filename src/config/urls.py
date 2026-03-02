from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("members/", include("apps.members.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("orders/", include("apps.orders.urls")),
    path("compliance/", include("apps.compliance.urls")),
    path("finance/", include("apps.finance.urls")),
]
