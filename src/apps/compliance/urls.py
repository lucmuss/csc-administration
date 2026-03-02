from django.urls import path

from .views import annual_report, dashboard, suspicious_activity_list

app_name = "compliance"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("annual-report/", annual_report, name="annual_report"),
    path("suspicious-activities/", suspicious_activity_list, name="suspicious_activity_list"),
]
