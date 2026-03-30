from __future__ import annotations

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils import timezone


def _request_meta(request: HttpRequest) -> tuple[str, str]:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "").strip()
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR", "").strip() or "unknown"
    user_agent = request.META.get("HTTP_USER_AGENT", "").strip() or "unknown device"
    return ip_address, user_agent


def _app_public_url() -> str:
    return (settings.SITE_URL or "http://localhost:8000").rstrip("/")


def _absolute_url(request: HttpRequest, route_name: str, fallback_path: str) -> str:
    try:
        return request.build_absolute_uri(reverse(route_name))
    except (NoReverseMatch, DisallowedHost):
        return f"{_app_public_url()}{fallback_path}"


def _render_subject(template_name: str, context: dict) -> str:
    raw = render_to_string(template_name, context)
    return " ".join(line.strip() for line in raw.splitlines() if line.strip())


def send_login_alert_email(user, request: HttpRequest) -> bool:
    ip_address, user_agent = _request_meta(request)
    context = {
        "user": user,
        "login_time": timezone.localtime(),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "dashboard_url": _absolute_url(request, "core:dashboard", "/"),
        "password_change_url": _absolute_url(
            request, "admin:password_change", "/admin/password_change/"
        ),
    }

    subject = _render_subject("emails/account/login_alert_subject.txt", context)
    text_body = render_to_string("emails/account/login_alert_body.txt", context)
    html_body = render_to_string("emails/account/login_alert_body.html", context)

    from_email = settings.DEFAULT_FROM_EMAIL
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    return msg.send(fail_silently=True) > 0


def send_registration_received_email(user, request: HttpRequest, *, is_bootstrap: bool = False) -> bool:
    context = {
        "user": user,
        "is_bootstrap": is_bootstrap,
        "login_url": _absolute_url(request, "accounts:login", "/accounts/login/"),
        "dashboard_url": _absolute_url(request, "core:dashboard", "/"),
    }

    subject = _render_subject("emails/account/registration_received_subject.txt", context)
    text_body = render_to_string("emails/account/registration_received_body.txt", context)
    html_body = render_to_string("emails/account/registration_received_body.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    return msg.send(fail_silently=True) > 0
