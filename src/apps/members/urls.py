from django.urls import path

from .views import (
    directory,
    export_members_csv,
    import_members_csv,
    member_action,
    member_detail,
    onboarding_view,
    profile_view,
    register,
    verification_detail,
    verification_view,
    verify_member,
)

app_name = "members"

urlpatterns = [
    path("register/", register, name="register"),
    path("onboarding/", onboarding_view, name="onboarding"),
    path("profile/", profile_view, name="profile"),
    path("verification/", verification_view, name="verification"),
    path("admin/", directory, name="directory"),
    path("admin/<int:profile_id>/", member_detail, name="detail"),
    path("admin/<int:profile_id>/verification/", verification_detail, name="verification_detail"),
    path("export/", export_members_csv, name="export"),
    path("import/", import_members_csv, name="import"),
    path("action/<int:profile_id>/", member_action, name="action"),
    path("verify/<int:profile_id>/", verify_member, name="verify"),
]
