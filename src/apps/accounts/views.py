from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

from .emails import send_login_alert_email
from .forms import EmailAuthenticationForm


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if getattr(self.request.user, "email", ""):
            send_login_alert_email(self.request.user, self.request)
        return response


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")
