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
    
    # SMS
    path("sms/", views.sms_list, name="sms_list"),
    path("sms/create/", views.sms_create, name="sms_create"),
    path("sms/<uuid:pk>/", views.sms_detail, name="sms_detail"),
    path("sms/<uuid:pk>/preview/", views.sms_preview, name="sms_preview"),
    path("sms/<uuid:pk>/edit/", views.sms_edit, name="sms_edit"),
    path("sms/<uuid:pk>/send/", views.sms_send, name="sms_send"),
    path("sms/<uuid:pk>/delete/", views.sms_delete, name="sms_delete"),
    
    # SMS Templates
    path("sms/templates/", views.sms_template_list, name="sms_template_list"),
    path("sms/templates/create/", views.sms_template_create, name="sms_template_create"),
    path("sms/templates/<uuid:pk>/edit/", views.sms_template_edit, name="sms_template_edit"),
    path("sms/templates/<uuid:pk>/delete/", views.sms_template_delete, name="sms_template_delete"),
    
    # SMS Providers
    path("sms/providers/", views.sms_provider_list, name="sms_provider_list"),
    path("sms/providers/create/", views.sms_provider_create, name="sms_provider_create"),
    path("sms/providers/<uuid:pk>/edit/", views.sms_provider_edit, name="sms_provider_edit"),
    path("sms/providers/<uuid:pk>/delete/", views.sms_provider_delete, name="sms_provider_delete"),
    
    # SMS Statistics
    path("sms/stats/", views.sms_stats, name="sms_stats"),
    
    # API
    path("api/groups/<int:pk>/members/", views.api_group_members, name="api_group_members"),
    path("api/emails/<uuid:pk>/stats/", views.api_email_stats, name="api_email_stats"),
    path("api/sms/character-count/", views.api_sms_character_count, name="api_sms_character_count"),
    path("api/sms/render-template/", views.api_render_sms_template, name="api_render_sms_template"),
    
    # Tracking
    path("track/<str:tracking_id>.gif", views.track_email_open, name="track_open"),
]
