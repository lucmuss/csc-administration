from django.urls import path

from .views import directory, export_members_csv, import_members_csv, member_action, member_detail, onboarding_view, profile_view, register, verify_member

app_name = "members"

urlpatterns = [
    path("register/", register, name="register"),
    path("onboarding/", onboarding_view, name="onboarding"),
    path("profile/", profile_view, name="profile"),
    path("admin/", directory, name="directory"),
    path("admin/<int:profile_id>/", member_detail, name="detail"),
    path("export/", export_members_csv, name="export"),
    path("import/", import_members_csv, name="import"),
    path("action/<int:profile_id>/", member_action, name="action"),
    path("verify/<int:profile_id>/", verify_member, name="verify"),
]
