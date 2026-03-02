from django.urls import path

from .views import EmailLoginView, UserLogoutView

app_name = "accounts"

urlpatterns = [
    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
]
