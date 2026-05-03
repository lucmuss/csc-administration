from django.urls import path
from django.views.generic import RedirectView

from .views import (
    club_settings_admin,
    dashboard,
    documents,
    documents_admin,
    health,
    imprint,
    public_preferences,
    privacy,
    pricing,
    ready,
    terms,
    social_club_review,
    social_club_admin,
    social_club_profile,
    social_club_public_detail,
    social_club_public_list,
    social_club_regional_list,
    social_club_register,
    switch_federal_state,
    switch_social_club,
)

app_name = "core"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("privacy/", privacy, name="privacy"),
    path("terms/", terms, name="terms"),
    path("imprint/", imprint, name="imprint"),
    path("documents/", documents, name="documents"),
    path("pricing/", pricing, name="pricing"),
    path("website-einstellungen/", public_preferences, name="public_preferences"),
    path("documents/admin/", documents_admin, name="documents_admin"),
    path("settings/club/", club_settings_admin, name="club_settings"),
    path("social-clubs/register/", social_club_register, name="social_club_register"),
    path("social-clubs/admin/", social_club_admin, name="social_club_admin"),
    path("social-clubs/profile/", social_club_profile, name="social_club_profile"),
    path("social-clubs/review/", social_club_review, name="social_club_review"),
    path("social-clubs/switch/", switch_social_club, name="social_club_switch"),
    path("social-clubs/regionen/", social_club_regional_list, name="social_club_regional_list"),
    path("social-clubs/bundesland/", switch_federal_state, name="social_club_state_switch"),
    path("social-clubs/", social_club_public_list, name="social_club_public_list"),
    path("social-clubs/<slug:slug>/", social_club_public_detail, name="social_club_public_detail"),
    path("impressum/", RedirectView.as_view(pattern_name="core:imprint", permanent=False)),
    path("impressum.html", RedirectView.as_view(pattern_name="core:imprint", permanent=False)),
    path("health/", health, name="health"),
    path("ready/", ready, name="ready"),
]
