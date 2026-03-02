from django.urls import path

from .views import admin_hours_view, dashboard_view, shift_calendar_view

app_name = "participation"

urlpatterns = [
    path("dashboard/", dashboard_view, name="dashboard"),
    path("shifts/", shift_calendar_view, name="shift_calendar"),
    path("admin/hours/", admin_hours_view, name="admin_hours"),
]
