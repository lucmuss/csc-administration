from django.urls import path

from .views import profile_view, register, verify_member

app_name = "members"

urlpatterns = [
    path("register/", register, name="register"),
    path("profile/", profile_view, name="profile"),
    path("verify/<int:profile_id>/", verify_member, name="verify"),
]
