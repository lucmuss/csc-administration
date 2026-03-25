from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse_lazy

from .emails import send_login_alert_email
from .forms import EmailAuthenticationForm
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


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


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
