# messaging/urls.py
from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    # Dashboard
    path("", views.messaging_dashboard, name="dashboard"),
    
    # Email Groups
    path("groups/", views.email_group_list, name="email_group_list"),
    path("groups/create/", views.email_group_create, name="email_group_create"),
    path("groups/<int:pk>/", views.email_group_detail, name="email_group_detail"),
    path("groups/<int:pk>/edit/", views.email_group_edit, name="email_group_edit"),
    path("groups/<int:pk>/delete/", views.email_group_delete, name="email_group_delete"),
    path("groups/<int:pk>/add-members/", views.email_group_add_members, name="email_group_add_members"),
    path("groups/<int:pk>/remove-member/<int:member_pk>/", views.email_group_remove_member, name="email_group_remove_member"),
    
    # Mass Emails
    path("emails/", views.mass_email_list, name="mass_email_list"),
    path("emails/create/", views.mass_email_create, name="mass_email_create"),
    path("emails/<uuid:pk>/", views.mass_email_detail, name="mass_email_detail"),
    path("emails/<uuid:pk>/preview/", views.mass_email_preview, name="mass_email_preview"),
    path("emails/<uuid:pk>/edit/", views.mass_email_edit, name="mass_email_edit"),
    path("emails/<uuid:pk>/send/", views.mass_email_send, name="mass_email_send"),
    path("emails/<uuid:pk>/delete/", views.mass_email_delete, name="mass_email_delete"),
    
    # API
    path("api/groups/<int:pk>/members/", views.api_group_members, name="api_group_members"),
    path("api/emails/<uuid:pk>/stats/", views.api_email_stats, name="api_email_stats"),
    
    # Tracking
    path("track/<str:tracking_id>.gif", views.track_email_open, name="track_open"),
]
