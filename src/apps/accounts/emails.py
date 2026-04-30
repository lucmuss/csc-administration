from __future__ import annotations

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from apps.core.club import get_club_settings


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


def _absolute_url_with_kwargs(request: HttpRequest, route_name: str, fallback_path: str, **kwargs) -> str:
    try:
        return request.build_absolute_uri(reverse(route_name, kwargs=kwargs))
    except (NoReverseMatch, DisallowedHost):
        return f"{_app_public_url()}{fallback_path}"


def _render_subject(template_name: str, context: dict) -> str:
    raw = render_to_string(template_name, context)
    return " ".join(line.strip() for line in raw.splitlines() if line.strip())


def _club_email_context() -> dict:
    return get_club_settings()


def _apply_email_signature(text_body: str, html_body: str, context: dict) -> tuple[str, str]:
    signature_text = (context.get("club_email_signature_text") or "").strip()
    signature_html = (context.get("club_email_signature_html") or "").strip()
    if signature_text:
        text_body = f"{text_body.rstrip()}\n\n-- \n{signature_text}\n"
    if signature_html:
        html_body = f"{html_body.rstrip()}<hr><div>{signature_html}</div>"
    return text_body, html_body


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
    context.update(_club_email_context())

    subject = _render_subject("emails/account/login_alert_subject.txt", context)
    text_body = render_to_string("emails/account/login_alert_body.txt", context)
    html_body = render_to_string("emails/account/login_alert_body.html", context)
    text_body, html_body = _apply_email_signature(text_body, html_body, context)

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
    context.update(_club_email_context())

    subject = _render_subject("emails/account/registration_received_subject.txt", context)
    text_body = render_to_string("emails/account/registration_received_body.txt", context)
    html_body = render_to_string("emails/account/registration_received_body.html", context)
    text_body, html_body = _apply_email_signature(text_body, html_body, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    return msg.send(fail_silently=True) > 0


def send_membership_status_email(
    user,
    request: HttpRequest,
    *,
    status_title: str,
    message: str,
    profile=None,
) -> bool:
    context = {
        "user": user,
        "status_title": status_title,
        "message": message,
        "login_url": _absolute_url(request, "accounts:login", "/accounts/login/"),
        "dashboard_url": _absolute_url(request, "core:dashboard", "/"),
        "profile": profile,
    }
    context.update(_club_email_context())

    subject = _render_subject("emails/account/member_status_update_subject.txt", context)
    text_body = render_to_string("emails/account/member_status_update_body.txt", context)
    html_body = render_to_string("emails/account/member_status_update_body.html", context)
    text_body, html_body = _apply_email_signature(text_body, html_body, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    return msg.send(fail_silently=True) > 0


def send_membership_documents_email(profile, request: HttpRequest) -> bool:
    from apps.members.documents import membership_document_attachments

    context = {
        "user": profile.user,
        "dashboard_url": _absolute_url(request, "core:dashboard", "/"),
        "login_url": _absolute_url(request, "accounts:login", "/accounts/login/"),
        "profile": profile,
    }
    context.update(_club_email_context())
    subject = _render_subject("emails/account/membership_documents_subject.txt", context)
    text_body = render_to_string("emails/account/membership_documents_body.txt", context)
    html_body = render_to_string("emails/account/membership_documents_body.html", context)
    text_body, html_body = _apply_email_signature(text_body, html_body, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[profile.user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    for filename, content, mimetype in membership_document_attachments(profile):
        msg.attach(filename, content, mimetype)
    return msg.send(fail_silently=True) > 0


def send_order_reserved_email(*, order, request: HttpRequest) -> bool:
    from apps.finance.services import balance_breakdown, render_invoice_pdf

    profile = order.member.profile
    invoice = getattr(order, "invoice", None)
    context = {
        "user": order.member,
        "order": order,
        "order_url": _absolute_url_with_kwargs(request, "orders:detail", f"/orders/my/{order.id}/", order_id=order.id),
        "balance_breakdown": balance_breakdown(profile),
    }
    context.update(_club_email_context())
    subject = _render_subject("emails/orders/reserved_subject.txt", context)
    text_body = render_to_string("emails/orders/reserved_body.txt", context)
    html_body = render_to_string("emails/orders/reserved_body.html", context)
    text_body, html_body = _apply_email_signature(text_body, html_body, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.member.email],
    )
    msg.attach_alternative(html_body, "text/html")
    if invoice:
        msg.attach(f"{invoice.invoice_number}.pdf", render_invoice_pdf(invoice), "application/pdf")
    return msg.send(fail_silently=True) > 0


def send_order_completed_email(*, order, request: HttpRequest) -> bool:
    from apps.finance.services import balance_breakdown, render_invoice_pdf

    profile = order.member.profile
    invoice = getattr(order, "invoice", None)
    context = {
        "user": order.member,
        "order": order,
        "order_url": _absolute_url_with_kwargs(request, "orders:detail", f"/orders/my/{order.id}/", order_id=order.id),
        "balance_breakdown": balance_breakdown(profile),
    }
    context.update(_club_email_context())
    subject = _render_subject("emails/orders/completed_subject.txt", context)
    text_body = render_to_string("emails/orders/completed_body.txt", context)
    html_body = render_to_string("emails/orders/completed_body.html", context)
    text_body, html_body = _apply_email_signature(text_body, html_body, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.member.email],
    )
    msg.attach_alternative(html_body, "text/html")
    if invoice:
        msg.attach(f"{invoice.invoice_number}.pdf", render_invoice_pdf(invoice), "application/pdf")
    return msg.send(fail_silently=True) > 0


def send_verification_reminder_email(user, profile) -> bool:
    verification_url = f"{_app_public_url()}/members/verification/"
    context = {
        "user": user,
        "profile": profile,
        "verification_url": verification_url,
        "dashboard_url": f"{_app_public_url()}/",
    }
    context.update(_club_email_context())
    subject = _render_subject("emails/account/verification_reminder_subject.txt", context)
    text_body = render_to_string("emails/account/verification_reminder_body.txt", context)
    html_body = render_to_string("emails/account/verification_reminder_body.html", context)
    text_body, html_body = _apply_email_signature(text_body, html_body, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    return msg.send(fail_silently=True) > 0
