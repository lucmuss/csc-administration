from django.urls import path

from .views import directory, export_members_csv, member_action, profile_view, register, verify_member

app_name = "members"

urlpatterns = [
    path("register/", register, name="register"),
    path("profile/", profile_view, name="profile"),
    path("admin/", directory, name="directory"),
    path("export/", export_members_csv, name="export"),
    path("action/<int:profile_id>/", member_action, name="action"),
    path("verify/<int:profile_id>/", verify_member, name="verify"),
]
