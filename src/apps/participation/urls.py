from django.urls import path

from .views import admin_hours_view, dashboard_view, shift_calendar_view, shift_create_view, shift_detail_view

app_name = "participation"

urlpatterns = [
    path("dashboard/", dashboard_view, name="dashboard"),
    path("shifts/", shift_calendar_view, name="shift_calendar"),
    path("shifts/new/", shift_create_view, name="shift_create"),
    path("shifts/<int:pk>/", shift_detail_view, name="shift_detail"),
    path("admin/hours/", admin_hours_view, name="admin_hours"),
]
