from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.auth import login
from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import add_never_cache_headers
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse
from django.urls import reverse_lazy

from .emails import send_login_alert_email
from .forms import EmailAuthenticationForm, StyledPasswordResetForm, StyledSetPasswordForm
from .models import User
from apps.core.club import (
    ACTIVE_FEDERAL_STATE_COOKIE,
    ACTIVE_FEDERAL_STATE_SESSION_KEY,
    ACTIVE_SOCIAL_CLUB_COOKIE,
    ACTIVE_SOCIAL_CLUB_SESSION_KEY,
    resolve_active_federal_state,
    resolve_active_social_club,
)


def _member_restricted_prefixes() -> tuple[str, ...]:
    return (
        reverse("members:directory"),
        reverse("orders:admin_list"),
        reverse("inventory:strain_list").rsplit("/", 1)[0] + "/",
        reverse("messaging:dashboard"),
        reverse("compliance:dashboard"),
        reverse("governance:dashboard"),
        reverse("core:documents_admin"),
        reverse("finance:archive"),
        reverse("finance:statistics"),
        reverse("cultivation:dashboard"),
    )


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return (request.META.get("REMOTE_ADDR") or "").strip()


def _login_limit_key(ip_address: str, username: str) -> str:
    return f"login-rate-limit:{ip_address}:{username.strip().lower()}"


def _restricted_redirect_for_user(request: HttpRequest, redirect_to: str) -> bool:
    if not redirect_to:
        return False
    if request.user.role in {User.ROLE_STAFF, User.ROLE_BOARD}:
        return False
    return any(redirect_to.startswith(prefix) for prefix in _member_restricted_prefixes())


@method_decorator(never_cache, name="dispatch")
class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", "").strip().lower()
        if self._is_rate_limited(request, username):
            form = self.get_form()
            form.add_error(None, "Zu viele fehlgeschlagene Anmeldeversuche. Bitte warte kurz und versuche es erneut.")
            return super().form_invalid(form)
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        active_club = resolve_active_social_club(self.request)
        active_state = resolve_active_federal_state(self.request)
        if active_club:
            initial["social_club"] = active_club.id
        if active_state:
            initial["federal_state"] = active_state
        return initial

    def form_valid(self, form):
        self._clear_rate_limit(self.request, form.cleaned_data.get("username", ""))
        response = super().form_valid(form)
        selected_club = form.cleaned_data.get("social_club")
        if selected_club:
            self.request.session[ACTIVE_SOCIAL_CLUB_SESSION_KEY] = selected_club.id
            self.request.session.modified = True
            response.set_cookie(ACTIVE_SOCIAL_CLUB_COOKIE, str(selected_club.id), max_age=60 * 60 * 24 * 365, samesite="Lax")
        selected_state = (form.cleaned_data.get("federal_state") or "").strip()
        if selected_state:
            self.request.session[ACTIVE_FEDERAL_STATE_SESSION_KEY] = selected_state
            self.request.session.modified = True
            response.set_cookie(ACTIVE_FEDERAL_STATE_COOKIE, selected_state, max_age=60 * 60 * 24 * 365, samesite="Lax")
        if getattr(self.request.user, "email", ""):
            send_login_alert_email(self.request.user, self.request)
        return response

    def form_invalid(self, form):
        self._register_failed_attempt(self.request, self.request.POST.get("username", ""))
        return super().form_invalid(form)

    def get_success_url(self):
        profile = getattr(self.request.user, "profile", None)
        if profile is not None and not profile.onboarding_complete:
            return reverse("members:onboarding")
        redirect_to = self.get_redirect_url()
        if _restricted_redirect_for_user(self.request, redirect_to):
            return reverse("core:dashboard")
        return redirect_to or super().get_success_url()

    def _is_rate_limited(self, request, username: str) -> bool:
        attempts = getattr(settings, "LOGIN_RATE_LIMIT_ATTEMPTS", 5)
        if attempts <= 0 or not username:
            return False
        key = _login_limit_key(_client_ip(request), username)
        return int(cache.get(key, 0)) >= attempts

    def _register_failed_attempt(self, request, username: str) -> None:
        attempts = getattr(settings, "LOGIN_RATE_LIMIT_ATTEMPTS", 5)
        window = getattr(settings, "LOGIN_RATE_LIMIT_WINDOW_SECONDS", 900)
        if attempts <= 0 or window <= 0 or not username:
            return
        key = _login_limit_key(_client_ip(request), username)
        current = int(cache.get(key, 0)) + 1
        cache.set(key, current, timeout=window)

    def _clear_rate_limit(self, request, username: str) -> None:
        if not username:
            return
        cache.delete(_login_limit_key(_client_ip(request), username))


@method_decorator(never_cache, name="dispatch")
class UserLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        add_never_cache_headers(response)
        response.delete_cookie(settings.CSRF_COOKIE_NAME)
        response.headers.setdefault("Clear-Site-Data", '"cache", "cookies", "storage"')
        return response


@method_decorator(never_cache, name="dispatch")
class MemberPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")
    form_class = StyledPasswordResetForm


@method_decorator(never_cache, name="dispatch")
class MemberPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


@method_decorator(never_cache, name="dispatch")
class MemberPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
    form_class = StyledSetPasswordForm


@method_decorator(never_cache, name="dispatch")
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
