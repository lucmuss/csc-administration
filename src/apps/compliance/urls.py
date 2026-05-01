from django.urls import path

from .views import annual_report, bopst_report, dashboard, member_export, suspicious_activity_list

app_name = "compliance"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("annual-report/", annual_report, name="annual_report"),
    path("bopst-report/", bopst_report, name="bopst_report"),
    path("member-export/", member_export, name="member_export"),
    path("suspicious-activities/", suspicious_activity_list, name="suspicious_activity_list"),
]
