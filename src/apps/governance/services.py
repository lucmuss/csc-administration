import io
import json
from datetime import timedelta
from urllib import error, request as urllib_request
from uuid import uuid4

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.finance.models import Invoice
from apps.members.models import Profile

from .models import AuditLog, BoardMeeting, BoardTask, IntegrationDelivery, IntegrationEndpoint, MemberCard, OperationalRecord


def record_audit_event(*, actor=None, domain: str, action: str, summary: str, target=None, metadata=None, request=None):
    metadata = metadata or {}
    previous = AuditLog.objects.order_by("-created_at", "-id").first()
    entry = AuditLog.objects.create(
        actor=actor,
        domain=domain,
        action=action,
        target_model=target.__class__.__name__ if target else "",
        target_id=str(getattr(target, "pk", "")) if target else "",
        summary=summary,
        metadata=metadata,
        ip_address=_request_ip(request),
        previous_hash=previous.entry_hash if previous else "",
    )
    payload = {
        "event": f"{domain}.{action}",
        "created_at": entry.created_at.isoformat(),
        "summary": summary,
        "target_model": entry.target_model,
        "target_id": entry.target_id,
        "actor": getattr(actor, "email", "system"),
        "metadata": metadata,
    }
    dispatch_webhook_event(event_name=payload["event"], payload=payload)
    return entry


def _request_ip(request):
    if not request:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def issue_member_card(*, profile: Profile, issued_by=None, expires_at=None, notes: str = ""):
    expires_at = expires_at or (timezone.localdate() + timedelta(days=365))
    card, created = MemberCard.objects.get_or_create(
        profile=profile,
        defaults={
            "card_number": f"CARD-{profile.member_number or profile.id}-{uuid4().hex[:6].upper()}",
            "issued_by": issued_by,
            "expires_at": expires_at,
            "notes": notes,
        },
    )
    if not created:
        card.version += 1
        card.qr_token = uuid4().hex
        card.issued_by = issued_by
        card.issued_at = timezone.now()
        card.expires_at = expires_at
        card.notes = notes
        card.status = MemberCard.STATUS_ACTIVE
        card.save()
    return card


def _site_url() -> str:
    return (settings.SITE_URL or "http://localhost:8000").rstrip("/")


def _eligible_meeting_profiles():
    return Profile.objects.select_related("user").filter(
        status__in=[Profile.STATUS_ACTIVE, Profile.STATUS_VERIFIED],
        is_verified=True,
    )


def _meeting_context(meeting: BoardMeeting) -> dict:
    agenda_deadline = meeting.scheduled_for - timedelta(days=7)
    return {
        "meeting": meeting,
        "meeting_url": meeting.participation_url or meeting.location or "",
        "minutes_url": meeting.minutes_url,
        "meeting_date": timezone.localtime(meeting.scheduled_for),
        "agenda_deadline": timezone.localtime(agenda_deadline),
        "agenda_submission_email": meeting.agenda_submission_email or settings.GENERAL_MEETING_AGENDA_SUBMISSION_EMAIL,
        "club_contact_email": settings.CLUB_CONTACT_EMAIL,
        "club_contact_phone": settings.CLUB_CONTACT_PHONE,
        "club_contact_address": settings.CLUB_CONTACT_ADDRESS,
        "dashboard_url": f"{_site_url()}{reverse('governance:meetings')}",
    }


def _send_meeting_message(*, meeting: BoardMeeting, subject: str, text_template: str, html_template: str) -> int:
    sent = 0
    base_context = _meeting_context(meeting)
    for profile in _eligible_meeting_profiles():
        context = {**base_context, "profile": profile, "user": profile.user}
        text_body = render_to_string(text_template, context)
        html_body = render_to_string(html_template, context)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[profile.user.email],
        )
        msg.attach_alternative(html_body, "text/html")
        sent += int(msg.send(fail_silently=True) > 0)
    return sent


def send_general_meeting_invitation(*, meeting: BoardMeeting) -> int:
    if meeting.meeting_type != BoardMeeting.TYPE_GENERAL:
        return 0
    sent = _send_meeting_message(
        meeting=meeting,
        subject=f"Einladung zur Mitgliederversammlung: {meeting.title}",
        text_template="emails/governance/meeting_invitation_body.txt",
        html_template="emails/governance/meeting_invitation_body.html",
    )
    meeting.invitation_sent_at = timezone.now()
    meeting.save(update_fields=["invitation_sent_at", "updated_at"])
    return sent


def send_general_meeting_reminder(*, meeting: BoardMeeting) -> int:
    if meeting.meeting_type != BoardMeeting.TYPE_GENERAL:
        return 0
    sent = _send_meeting_message(
        meeting=meeting,
        subject=f"Erinnerung: Mitgliederversammlung {meeting.title}",
        text_template="emails/governance/meeting_reminder_body.txt",
        html_template="emails/governance/meeting_reminder_body.html",
    )
    meeting.reminder_sent_at = timezone.now()
    meeting.save(update_fields=["reminder_sent_at", "updated_at"])
    return sent


def send_due_meeting_notifications(*, now=None) -> dict[str, int]:
    now = now or timezone.now()
    invitations = 0
    reminders = 0
    meetings = BoardMeeting.objects.filter(
        meeting_type=BoardMeeting.TYPE_GENERAL,
        status=BoardMeeting.STATUS_PLANNED,
    )
    for meeting in meetings:
        invitation_due = meeting.scheduled_for - timedelta(days=meeting.invitation_lead_days)
        reminder_due = meeting.scheduled_for - timedelta(hours=meeting.reminder_lead_hours)
        if not meeting.invitation_sent_at and invitation_due <= now:
            invitations += send_general_meeting_invitation(meeting=meeting)
        if not meeting.reminder_sent_at and reminder_due <= now:
            reminders += send_general_meeting_reminder(meeting=meeting)
    return {"invitations": invitations, "reminders": reminders}


def member_card_qr_svg(card: MemberCard, validation_url: str) -> str:
    import segno

    qr = segno.make(validation_url, error="m")
    return qr.svg_inline(scale=4, dark="#163526", light="#ffffff")


def render_operational_record_pdf(record: OperationalRecord) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=A4)
    width, height = A4

    pdf.setTitle(record.reference)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(20 * mm, height - 25 * mm, record.get_record_type_display())
    pdf.setFont("Helvetica", 10)

    lines = [
        ("Referenz", record.reference),
        ("Status", record.get_status_display()),
        ("Menge", f"{record.quantity_grams} g"),
        ("Sorte", record.strain.name if record.strain else "-"),
        ("Mitglied", record.related_member.user.full_name if record.related_member else "-"),
        ("Ursprung", record.origin or "-"),
        ("Ziel", record.destination or "-"),
        ("Operator", record.operator_name or "-"),
        ("Zeuge", record.witness_name or "-"),
        ("Fahrzeug", record.vehicle_identifier or "-"),
        ("Vernichtungsmethode", record.destruction_method or "-"),
        ("Durchgefuehrt am", timezone.localtime(record.executed_at).strftime("%d.%m.%Y %H:%M") if record.executed_at else "-"),
        ("Freigegeben von", record.approved_by.full_name if record.approved_by else "-"),
    ]

    y = height - 40 * mm
    for label, value in lines:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(20 * mm, y, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(60 * mm, y, str(value))
        y -= 7 * mm

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20 * mm, y - 4 * mm, "Notizen")
    text = pdf.beginText(20 * mm, y - 12 * mm)
    text.setFont("Helvetica", 10)
    for line in (record.notes or "Keine zusaetzlichen Hinweise.").splitlines()[:18]:
        text.textLine(line)
    pdf.drawText(text)

    pdf.showPage()
    pdf.save()
    return stream.getvalue()


def dispatch_webhook_event(*, event_name: str, payload: dict):
    endpoints = IntegrationEndpoint.objects.filter(enabled=True).exclude(endpoint_url="")
    for endpoint in endpoints:
        if endpoint.subscribed_events and event_name not in endpoint.subscribed_events and "*" not in endpoint.subscribed_events:
            continue

        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if endpoint.auth_token:
            headers[endpoint.auth_header_name] = endpoint.auth_token
        req = urllib_request.Request(endpoint.endpoint_url, data=body, headers=headers, method="POST")

        status_code = None
        excerpt = ""
        error_message = ""
        try:
            with urllib_request.urlopen(req, timeout=5) as response:
                status_code = response.status
                excerpt = response.read(180).decode("utf-8", errors="ignore")
                endpoint.last_delivery_status = f"HTTP {status_code}"
        except error.HTTPError as exc:
            status_code = exc.code
            excerpt = exc.read(180).decode("utf-8", errors="ignore")
            error_message = f"HTTPError {exc.code}"
            endpoint.last_delivery_status = error_message
        except Exception as exc:
            error_message = str(exc)
            endpoint.last_delivery_status = "Fehlgeschlagen"

        endpoint.last_delivery_at = timezone.now()
        endpoint.last_error = error_message
        endpoint.save(update_fields=["last_delivery_at", "last_delivery_status", "last_error", "updated_at"])
        IntegrationDelivery.objects.create(
            endpoint=endpoint,
            event_name=event_name,
            payload=payload,
            status_code=status_code,
            response_excerpt=excerpt[:255],
        )


def api_response_for_resource(resource: str):
    if resource == "members":
        items = Profile.objects.select_related("user").order_by("member_number")
        return {
            "resource": resource,
            "items": [
                {
                    "member_number": profile.member_number,
                    "name": profile.user.full_name,
                    "email": profile.user.email,
                    "status": profile.status,
                    "verified": profile.is_verified,
                }
                for profile in items
            ],
        }

    if resource == "invoices":
        invoices = Invoice.objects.select_related("profile__user").order_by("-created_at")[:200]
        return {
            "resource": resource,
            "items": [
                {
                    "invoice_number": invoice.invoice_number,
                    "member": invoice.profile.user.email,
                    "amount": str(invoice.amount),
                    "status": invoice.status,
                    "due_date": invoice.due_date.isoformat(),
                }
                for invoice in invoices
            ],
        }

    if resource == "tasks":
        tasks = BoardTask.objects.select_related("owner").order_by("due_date", "-created_at")
        return {
            "resource": resource,
            "items": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "owner": task.owner.email if task.owner else "",
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                }
                for task in tasks
            ],
        }

    if resource == "records":
        records = OperationalRecord.objects.select_related("strain", "related_member__user").order_by("-created_at")[:200]
        return {
            "resource": resource,
            "items": [
                {
                    "reference": record.reference,
                    "type": record.record_type,
                    "status": record.status,
                    "quantity_grams": str(record.quantity_grams),
                    "strain": record.strain.name if record.strain else "",
                    "member": record.related_member.user.email if record.related_member else "",
                }
                for record in records
            ],
        }

    raise ValueError("Unbekannte API-Ressource")


def integration_allows_resource(api_key: str, resource: str):
    endpoint = IntegrationEndpoint.objects.filter(api_key=api_key, enabled=True).first()
    if not endpoint:
        return None
    if endpoint.resource_scope and resource not in endpoint.resource_scope and "*" not in endpoint.resource_scope:
        return None
    return endpoint


def json_api_response(resource: str):
    payload = api_response_for_resource(resource)
    return JsonResponse(payload)
