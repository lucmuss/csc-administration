from django.urls import path

from .views import (
    EmailLoginView,
    MemberPasswordChangeDoneView,
    MemberPasswordChangeView,
    MemberPasswordResetCompleteView,
    MemberPasswordResetConfirmView,
    MemberPasswordResetDoneView,
    MemberPasswordResetView,
    UserLogoutView,
    dev_login,
    legacy_register,
)

app_name = "accounts"

urlpatterns = [
    path("login/", EmailLoginView.as_view(), name="login"),
    path("register/", legacy_register, name="register"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("password-reset/", MemberPasswordResetView.as_view(), name="password_reset"),
    path("password/change/", MemberPasswordChangeView.as_view(), name="password_change"),
    path("password/change/done/", MemberPasswordChangeDoneView.as_view(), name="password_change_done"),
    path("password-reset/done/", MemberPasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "reset/<uidb64>/<token>/",
        MemberPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        MemberPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("dev-login/", dev_login, name="dev_login"),
]
