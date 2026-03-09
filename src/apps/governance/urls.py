from django.urls import path

from .views import (
    api_export,
    audit_log,
    card_detail,
    cards,
    dashboard,
    integrations,
    meeting_detail,
    meetings,
    record_pdf,
    records,
    tasks,
    validate_card,
)

app_name = "governance"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("meetings/", meetings, name="meetings"),
    path("meetings/<int:pk>/", meeting_detail, name="meeting_detail"),
    path("tasks/", tasks, name="tasks"),
    path("cards/", cards, name="cards"),
    path("cards/<int:pk>/", card_detail, name="card_detail"),
    path("cards/validate/<str:token>/", validate_card, name="card_validate"),
    path("records/", records, name="records"),
    path("records/<int:pk>/pdf/", record_pdf, name="record_pdf"),
    path("audit/", audit_log, name="audit_log"),
    path("integrations/", integrations, name="integrations"),
    path("api/<str:resource>/", api_export, name="api_export"),
]
