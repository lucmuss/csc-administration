from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.core.authz import staff_or_board_required

from .forms import (
    AuditLogFilterForm,
    BoardMeetingForm,
    BoardTaskForm,
    IntegrationEndpointForm,
    MeetingAgendaItemForm,
    MeetingResolutionForm,
    MemberCardIssueForm,
    OperationalRecordForm,
)
from .models import (
    AuditLog,
    BoardMeeting,
    BoardTask,
    IntegrationEndpoint,
    MemberCard,
    OperationalRecord,
)
from .services import (
    integration_allows_resource,
    issue_member_card,
    json_api_response,
    member_card_qr_svg,
    record_audit_event,
    render_operational_record_pdf,
    send_due_meeting_notifications,
    send_general_meeting_invitation,
    send_general_meeting_reminder,
)


def _is_staff_or_board(user: User) -> bool:
    return user.is_authenticated and user.role in {User.ROLE_STAFF, User.ROLE_BOARD}


@staff_or_board_required(_is_staff_or_board)
def dashboard(request):
    send_due_meeting_notifications()
    now = timezone.now()
    context = {
        "upcoming_meetings": BoardMeeting.objects.order_by("scheduled_for")[:6],
        "open_tasks": BoardTask.objects.exclude(status=BoardTask.STATUS_DONE).select_related("owner")[:8],
        "pending_records": OperationalRecord.objects.exclude(status=OperationalRecord.STATUS_EXECUTED)[:8],
        "expiring_cards": MemberCard.objects.select_related("profile__user").filter(expires_at__lte=timezone.localdate() + timedelta(days=30))[:8],
        "recent_audit_entries": AuditLog.objects.select_related("actor")[:10],
        "integrations": IntegrationEndpoint.objects.filter(enabled=True)[:6],
        "task_counts": {
            status: BoardTask.objects.filter(status=status).count()
            for status, _ in BoardTask.STATUS_CHOICES
        },
        "meeting_counts": {
            status: BoardMeeting.objects.filter(status=status).count()
            for status, _ in BoardMeeting.STATUS_CHOICES
        },
        "now": now,
    }
    return render(request, "governance/dashboard.html", context)


@staff_or_board_required(_is_staff_or_board)
def meetings(request):
    if request.method == "POST":
        form = BoardMeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.created_by = request.user
            if not meeting.agenda_submission_email:
                meeting.agenda_submission_email = settings.GENERAL_MEETING_AGENDA_SUBMISSION_EMAIL or request.user.email
            meeting.save()
            record_audit_event(
                actor=request.user,
                domain="governance",
                action="meeting.created",
                target=meeting,
                summary=f"Sitzung {meeting.title} angelegt.",
                metadata={"meeting_type": meeting.meeting_type},
                request=request,
            )
            messages.success(request, "Sitzung angelegt.")
            return redirect("governance:meeting_detail", pk=meeting.pk)
    else:
        form = BoardMeetingForm(
            initial={
                "meeting_type": BoardMeeting.TYPE_GENERAL,
                "chairperson": request.user,
                "location": "Online-Meeting",
                "invitation_lead_days": settings.GENERAL_MEETING_INVITATION_LEAD_DAYS,
                "reminder_lead_hours": settings.GENERAL_MEETING_REMINDER_LEAD_HOURS,
                "agenda_submission_email": settings.GENERAL_MEETING_AGENDA_SUBMISSION_EMAIL,
            }
        )

    return render(
        request,
        "governance/meetings.html",
        {"form": form, "meetings": BoardMeeting.objects.select_related("chairperson").order_by("-scheduled_for")},
    )


@staff_or_board_required(_is_staff_or_board)
def meeting_detail(request, pk: int):
    meeting = get_object_or_404(BoardMeeting.objects.select_related("chairperson"), pk=pk)
    meeting_form = BoardMeetingForm(instance=meeting)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update":
            meeting_form = BoardMeetingForm(request.POST, instance=meeting)
            agenda_form = MeetingAgendaItemForm(initial={"order": meeting.agenda_items.count() + 1})
            resolution_form = MeetingResolutionForm()
            resolution_form.fields["agenda_item"].queryset = meeting.agenda_items.all()
            if meeting_form.is_valid():
                meeting_form.save()
                messages.success(request, "Versammlungsdaten aktualisiert.")
                return redirect("governance:meeting_detail", pk=meeting.pk)
        elif action == "agenda":
            agenda_form = MeetingAgendaItemForm(request.POST)
            resolution_form = MeetingResolutionForm(initial={"agenda_item": meeting.agenda_items.first()})
            meeting_form = BoardMeetingForm(instance=meeting)
            if agenda_form.is_valid():
                item = agenda_form.save(commit=False)
                item.meeting = meeting
                item.save()
                record_audit_event(
                    actor=request.user,
                    domain="governance",
                    action="agenda.created",
                    target=item,
                    summary=f"TOP {item.order} fuer {meeting.title} angelegt.",
                    metadata={"meeting_id": meeting.id},
                    request=request,
                )
                messages.success(request, "Tagesordnungspunkt gespeichert.")
                return redirect("governance:meeting_detail", pk=meeting.pk)
        elif action == "resolution":
            agenda_form = MeetingAgendaItemForm(initial={"order": meeting.agenda_items.count() + 1})
            resolution_form = MeetingResolutionForm(request.POST)
            meeting_form = BoardMeetingForm(instance=meeting)
            resolution_form.fields["agenda_item"].queryset = meeting.agenda_items.all()
            if resolution_form.is_valid():
                resolution = resolution_form.save(commit=False)
                resolution.meeting = meeting
                resolution.created_by = request.user
                resolution.save()
                record_audit_event(
                    actor=request.user,
                    domain="governance",
                    action="resolution.created",
                    target=resolution,
                    summary=f"Beschluss {resolution.resolution_number} fuer {meeting.title} erfasst.",
                    metadata={"status": resolution.status},
                    request=request,
                )
                messages.success(request, "Beschluss gespeichert.")
                return redirect("governance:meeting_detail", pk=meeting.pk)
        elif action == "send_invitation":
            agenda_form = MeetingAgendaItemForm(initial={"order": meeting.agenda_items.count() + 1})
            resolution_form = MeetingResolutionForm()
            resolution_form.fields["agenda_item"].queryset = meeting.agenda_items.all()
            meeting_form = BoardMeetingForm(instance=meeting)
            sent = send_general_meeting_invitation(meeting=meeting)
            record_audit_event(
                actor=request.user,
                domain="governance",
                action="meeting.invited",
                target=meeting,
                summary=f"Einladung fuer {meeting.title} versendet.",
                request=request,
            )
            messages.success(request, f"Einladung an {sent} Mitglieder versendet.")
            return redirect("governance:meeting_detail", pk=meeting.pk)
        elif action == "send_reminder":
            agenda_form = MeetingAgendaItemForm(initial={"order": meeting.agenda_items.count() + 1})
            resolution_form = MeetingResolutionForm()
            resolution_form.fields["agenda_item"].queryset = meeting.agenda_items.all()
            meeting_form = BoardMeetingForm(instance=meeting)
            sent = send_general_meeting_reminder(meeting=meeting)
            record_audit_event(
                actor=request.user,
                domain="governance",
                action="meeting.reminded",
                target=meeting,
                summary=f"Reminder fuer {meeting.title} versendet.",
                request=request,
            )
            messages.success(request, f"Reminder an {sent} Mitglieder versendet.")
            return redirect("governance:meeting_detail", pk=meeting.pk)
        elif action == "complete":
            agenda_form = MeetingAgendaItemForm(initial={"order": meeting.agenda_items.count() + 1})
            resolution_form = MeetingResolutionForm()
            resolution_form.fields["agenda_item"].queryset = meeting.agenda_items.all()
            meeting_form = BoardMeetingForm(instance=meeting)
            meeting.status = BoardMeeting.STATUS_COMPLETED
            meeting.minutes_summary = request.POST.get("minutes_summary", meeting.minutes_summary)
            meeting.attendance_notes = request.POST.get("attendance_notes", meeting.attendance_notes)
            meeting.save(update_fields=["status", "minutes_summary", "attendance_notes", "updated_at"])
            record_audit_event(
                actor=request.user,
                domain="governance",
                action="meeting.completed",
                target=meeting,
                summary=f"Sitzung {meeting.title} abgeschlossen.",
                request=request,
            )
            messages.success(request, "Sitzung abgeschlossen.")
            return redirect("governance:meeting_detail", pk=meeting.pk)
    else:
        agenda_form = MeetingAgendaItemForm(initial={"order": meeting.agenda_items.count() + 1})
        resolution_form = MeetingResolutionForm()

    resolution_form.fields["agenda_item"].queryset = meeting.agenda_items.all()
    return render(
        request,
        "governance/meeting_detail.html",
        {
            "meeting": meeting,
            "meeting_form": meeting_form,
            "agenda_form": agenda_form,
            "resolution_form": resolution_form,
            "agenda_items": meeting.agenda_items.select_related("owner"),
            "resolutions": meeting.resolutions.select_related("agenda_item", "created_by"),
        },
    )


@staff_or_board_required(_is_staff_or_board)
def tasks(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            form = BoardTaskForm(request.POST)
            if form.is_valid():
                task = form.save(commit=False)
                task.created_by = request.user
                task.save()
                record_audit_event(
                    actor=request.user,
                    domain="governance",
                    action="task.created",
                    target=task,
                    summary=f"Aufgabe {task.title} angelegt.",
                    metadata={"priority": task.priority},
                    request=request,
                )
                messages.success(request, "Aufgabe angelegt.")
                return redirect("governance:tasks")
        elif action == "status":
            task = get_object_or_404(BoardTask, pk=request.POST.get("task_id"))
            task.status = request.POST.get("status", task.status)
            task.save()
            record_audit_event(
                actor=request.user,
                domain="governance",
                action="task.updated",
                target=task,
                summary=f"Status von {task.title} auf {task.get_status_display()} gesetzt.",
                metadata={"status": task.status},
                request=request,
            )
            messages.success(request, "Aufgabenstatus aktualisiert.")
            return redirect("governance:tasks")
        elif action == "delete":
            task = get_object_or_404(BoardTask, pk=request.POST.get("task_id"))
            title = task.title
            record_audit_event(
                actor=request.user,
                domain="governance",
                action="task.deleted",
                target=task,
                summary=f"Aufgabe {title} geloescht.",
                request=request,
            )
            task.delete()
            messages.warning(request, "Aufgabe geloescht.")
            return redirect("governance:tasks")
    else:
        form = BoardTaskForm(
            initial={
                "status": BoardTask.STATUS_TODO,
                "owner": request.user,
                "due_date": timezone.localdate() + timedelta(days=5),
            }
        )

    task_columns = [
        {
            "status": status,
            "label": label,
            "tasks": BoardTask.objects.filter(status=status).select_related("owner"),
        }
        for status, label in BoardTask.STATUS_CHOICES
    ]
    return render(request, "governance/tasks.html", {"form": form, "task_columns": task_columns, "status_choices": BoardTask.STATUS_CHOICES})


@staff_or_board_required(_is_staff_or_board)
def cards(request):
    if request.method == "POST":
        form = MemberCardIssueForm(request.POST)
        if form.is_valid():
            card = issue_member_card(
                profile=form.cleaned_data["profile"],
                issued_by=request.user,
                expires_at=form.cleaned_data["expires_at"],
                notes=form.cleaned_data["notes"],
            )
            record_audit_event(
                actor=request.user,
                domain="governance",
                action="card.issued",
                target=card,
                summary=f"Mitgliedsausweis {card.card_number} ausgegeben.",
                metadata={"profile_id": card.profile_id, "version": card.version},
                request=request,
            )
            messages.success(request, "Mitgliedsausweis erstellt oder erneuert.")
            return redirect("governance:card_detail", pk=card.pk)
    else:
        form = MemberCardIssueForm(initial={"expires_at": timezone.localdate() + timedelta(days=365)})

    return render(
        request,
        "governance/cards.html",
        {
            "form": form,
            "cards": MemberCard.objects.select_related("profile__user", "issued_by").order_by("profile__member_number"),
        },
    )


@staff_or_board_required(_is_staff_or_board)
def card_detail(request, pk: int):
    card = get_object_or_404(MemberCard.objects.select_related("profile__user", "issued_by"), pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "reissue":
            updated = issue_member_card(profile=card.profile, issued_by=request.user, expires_at=card.expires_at, notes=card.notes)
            record_audit_event(
                actor=request.user,
                domain="governance",
                action="card.reissued",
                target=updated,
                summary=f"Mitgliedsausweis {updated.card_number} neu ausgestellt.",
                metadata={"version": updated.version},
                request=request,
            )
            messages.success(request, "Ausweis neu ausgestellt.")
            return redirect("governance:card_detail", pk=updated.pk)
        if action == "revoke":
            card.status = MemberCard.STATUS_REVOKED
            card.save(update_fields=["status"])
            record_audit_event(
                actor=request.user,
                domain="governance",
                action="card.revoked",
                target=card,
                summary=f"Mitgliedsausweis {card.card_number} entzogen.",
                request=request,
            )
            messages.warning(request, "Ausweis entzogen.")
            return redirect("governance:card_detail", pk=card.pk)

    qr_svg = member_card_qr_svg(card, request.build_absolute_uri(f"/governance/cards/validate/{card.qr_token}/"))
    return render(request, "governance/card_detail.html", {"card": card, "qr_svg": qr_svg})


def validate_card(request, token: str):
    card = MemberCard.objects.select_related("profile__user").filter(qr_token=token).first()
    if not card:
        raise Http404("Unbekannter QR-Code")
    card.last_scanned_at = timezone.now()
    card.save(update_fields=["last_scanned_at"])
    return JsonResponse(
        {
            "valid": card.is_valid,
            "card_number": card.card_number,
            "member_number": card.profile.member_number,
            "member": card.profile.user.full_name,
            "status": card.status,
            "expires_at": card.expires_at.isoformat(),
        }
    )


@staff_or_board_required(_is_staff_or_board)
def records(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            form = OperationalRecordForm(request.POST)
            if form.is_valid():
                record = form.save(commit=False)
                record.created_by = request.user
                record.save()
                record_audit_event(
                    actor=request.user,
                    domain="governance",
                    action="record.created",
                    target=record,
                    summary=f"{record.get_record_type_display()} {record.reference} angelegt.",
                    metadata={"record_type": record.record_type},
                    request=request,
                )
                messages.success(request, "Nachweis angelegt.")
                return redirect("governance:records")
        elif action in {"approve", "execute"}:
            record = get_object_or_404(OperationalRecord, pk=request.POST.get("record_id"))
            if action == "approve":
                record.status = OperationalRecord.STATUS_APPROVED
                record.approved_by = request.user
                summary = f"Nachweis {record.reference} freigegeben."
                audit_action = "record.approved"
            else:
                record.status = OperationalRecord.STATUS_EXECUTED
                record.executed_at = timezone.now()
                summary = f"Nachweis {record.reference} als durchgefuehrt markiert."
                audit_action = "record.executed"
            record.save(update_fields=["status", "approved_by", "executed_at", "updated_at"])
            record_audit_event(
                actor=request.user,
                domain="governance",
                action=audit_action,
                target=record,
                summary=summary,
                request=request,
            )
            messages.success(request, "Nachweis aktualisiert.")
            return redirect("governance:records")
    else:
        form = OperationalRecordForm(initial={"record_type": OperationalRecord.TYPE_TRANSPORT})

    return render(
        request,
        "governance/records.html",
        {"form": form, "records": OperationalRecord.objects.select_related("strain", "related_member__user", "approved_by")},
    )


@staff_or_board_required(_is_staff_or_board)
def record_pdf(request, pk: int):
    record = get_object_or_404(OperationalRecord.objects.select_related("strain", "related_member__user", "approved_by"), pk=pk)
    pdf = render_operational_record_pdf(record)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{record.reference}.pdf"'
    return response


@staff_or_board_required(_is_staff_or_board)
def audit_log(request):
    logs = AuditLog.objects.select_related("actor")
    filter_form = AuditLogFilterForm(request.GET or None)
    if filter_form.is_valid() and filter_form.cleaned_data.get("domain"):
        logs = logs.filter(domain=filter_form.cleaned_data["domain"])
    return render(request, "governance/audit_log.html", {"logs": logs[:250], "filter_form": filter_form})


@staff_or_board_required(_is_staff_or_board)
def integrations(request):
    if request.method == "POST":
        form = IntegrationEndpointForm(request.POST)
        if form.is_valid():
            endpoint = form.save(commit=False)
            endpoint.created_by = request.user
            endpoint.save()
            record_audit_event(
                actor=request.user,
                domain="governance",
                action="integration.created",
                target=endpoint,
                summary=f"Integration {endpoint.name} gespeichert.",
                metadata={"integration_type": endpoint.integration_type},
                request=request,
            )
            messages.success(request, "Integration gespeichert.")
            return redirect("governance:integrations")
    else:
        form = IntegrationEndpointForm(initial={"subscribed_events_input": "*", "resource_scope_input": "members,invoices,tasks,records"})

    endpoints = IntegrationEndpoint.objects.prefetch_related("deliveries")
    api_resources = ["members", "invoices", "tasks", "records"]
    return render(
        request,
        "governance/integrations.html",
        {"form": form, "endpoints": endpoints, "api_resources": api_resources},
    )


def api_export(request, resource: str):
    api_key = request.headers.get("X-Api-Key") or request.GET.get("api_key")
    endpoint = integration_allows_resource(api_key=api_key or "", resource=resource)
    if not endpoint:
        return JsonResponse({"detail": "ungueltiger API-Schluessel oder Scope"}, status=403)
    endpoint.last_delivery_at = timezone.now()
    endpoint.last_delivery_status = f"API {resource} gelesen"
    endpoint.save(update_fields=["last_delivery_at", "last_delivery_status", "updated_at"])
    return json_api_response(resource)
