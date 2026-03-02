from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

from .forms import EmailAuthenticationForm


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")
