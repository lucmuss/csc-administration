from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.auth import login
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse
from django.urls import reverse_lazy

from .emails import send_login_alert_email
from .forms import EmailAuthenticationForm, StyledPasswordResetForm, StyledSetPasswordForm
from .models import User


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if getattr(self.request.user, "email", ""):
            send_login_alert_email(self.request.user, self.request)
        return response

    def get_success_url(self):
        profile = getattr(self.request.user, "profile", None)
        if profile is not None and not profile.onboarding_complete:
            return reverse("members:onboarding")
        return super().get_success_url()


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


class MemberPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")
    form_class = StyledPasswordResetForm


class MemberPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class MemberPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
    form_class = StyledSetPasswordForm


class MemberPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


def dev_login(request):
    """Dev-Login fuer lokale GUI-Tests - nur bei DEBUG=True und localhost"""
    if not settings.DEBUG:
        return HttpResponseForbidden("Dev-Login nur im Debug-Modus verfuegbar.")
    
    # Zusaetzlicher IP-Check fuer extra Sicherheit
    remote_addr = request.META.get('REMOTE_ADDR', '')
    if remote_addr not in ['127.0.0.1', '::1']:
        return HttpResponseForbidden("Dev-Login nur von localhost erlaubt.")
    
    test_email = getattr(settings, 'TEST_USER_EMAIL', None)
    if not test_email:
        return HttpResponseForbidden("TEST_USER_EMAIL nicht konfiguriert.")
    
    # Optional: Test-User muss bestimmtes Suffix haben
    allowed_domain = getattr(settings, "DEV_LOGIN_ALLOWED_DOMAIN", "@test.local")
    if not test_email.endswith(allowed_domain):
        return HttpResponseForbidden(f"Ungueltiger Test-User. Muss {allowed_domain} Domain haben.")
    
    try:
        user = User.objects.get(email=test_email)
        login(request, user)
        return redirect('core:dashboard')
    except User.DoesNotExist:
        return HttpResponseForbidden(f"Testuser {test_email} nicht gefunden.")
