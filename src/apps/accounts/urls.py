from django.urls import path

from .views import EmailLoginView, UserLogoutView, dev_login

app_name = "accounts"

urlpatterns = [
    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("dev-login/", dev_login, name="dev_login"),
]
