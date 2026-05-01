from django.urls import path

from .views import (
    approve_member_legacy,
    directory,
    export_members_csv,
    import_members_csv,
    member_action,
    member_card_pdf,
    member_detail_legacy,
    member_detail,
    onboarding_view,
    profile_edit_legacy,
    profile_edit_self,
    profile_view,
    reject_member_legacy,
    register,
    suspend_member_legacy,
    verification_detail,
    verification_view,
    verify_member,
    verify_member_legacy,
)

app_name = "members"

urlpatterns = [
    path("register/", register, name="register"),
    path("onboarding/", onboarding_view, name="onboarding"),
    path("profile/", profile_view, name="profile"),
    path("profile/member-card.pdf", member_card_pdf, name="member_card_pdf"),
    path("profile/edit/", profile_edit_self, name="profile_edit"),
    path("verification/", verification_view, name="verification"),
    path("admin/", directory, name="directory"),
    path("member-list/", directory, name="member_list"),
    path("admin/<int:profile_id>/", member_detail, name="detail"),
    path("member/<int:pk>/", member_detail_legacy, name="member_detail"),
    path("profile/edit/<int:pk>/", profile_edit_legacy, name="profile_edit"),
    path("admin/<int:profile_id>/verification/", verification_detail, name="verification_detail"),
    path("export/", export_members_csv, name="export"),
    path("import/", import_members_csv, name="import"),
    path("action/<int:profile_id>/", member_action, name="action"),
    path("verify/<int:profile_id>/", verify_member, name="verify"),
    path("approve/<int:pk>/", approve_member_legacy, name="approve"),
    path("reject/<int:pk>/", reject_member_legacy, name="reject"),
    path("verify-member/<int:pk>/", verify_member_legacy, name="verify"),
    path("suspend/<int:pk>/", suspend_member_legacy, name="suspend"),
]
