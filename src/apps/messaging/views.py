# messaging/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction, models
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
import uuid

from .models import EmailGroup, EmailGroupMember, MassEmail, EmailLog
from .forms import EmailGroupForm, EmailGroupMemberForm, MassEmailForm, MassEmailSendForm
from apps.members.models import Member


# ==================== DASHBOARD ====================

@login_required
@permission_required("messaging.view_massemail", raise_exception=True)
def messaging_dashboard(request):
    """Messaging Dashboard mit Übersicht"""
    from django.db.models import Count, Sum
    
    context = {
        "total_groups": EmailGroup.objects.filter(is_active=True).count(),
        "total_emails": MassEmail.objects.exclude(status="draft").count(),
        "total_recipients": MassEmail.objects.aggregate(
            total=Sum("total_recipients")
        )["total"] or 0,
    }
    return render(request, "messaging/dashboard.html", context)


# ==================== EMAIL GROUPS ====================

@login_required
@permission_required("messaging.view_emailgroup", raise_exception=True)
def email_group_list(request):
    """Liste aller E-Mail-Gruppen"""
    groups = EmailGroup.objects.prefetch_related("members").all()
    return render(request, "messaging/email_group_list.html", {"groups": groups})


@login_required
@permission_required("messaging.add_emailgroup", raise_exception=True)
def email_group_create(request):
    """Neue E-Mail-Gruppe erstellen"""
    if request.method == "POST":
        form = EmailGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            messages.success(request, f"Gruppe '{group.name}' wurde erstellt.")
            return redirect("messaging:email_group_detail", pk=group.pk)
    else:
        form = EmailGroupForm()
    
    return render(request, "messaging/email_group_form.html", {
        "form": form,
        "title": "Neue E-Mail-Gruppe"
    })


@login_required
@permission_required("messaging.view_emailgroup", raise_exception=True)
def email_group_detail(request, pk):
    """Detailansicht einer E-Mail-Gruppe"""
    group = get_object_or_404(EmailGroup.objects.prefetch_related("members__member"), pk=pk)
    available_members = Member.objects.filter(status="active").exclude(
        id__in=group.members.values_list("member_id", flat=True)
    ).order_by("last_name", "first_name")
    
    return render(request, "messaging/email_group_detail.html", {
        "group": group,
        "available_members": available_members
    })


@login_required
@permission_required("messaging.change_emailgroup", raise_exception=True)
def email_group_edit(request, pk):
    """E-Mail-Gruppe bearbeiten"""
    group = get_object_or_404(EmailGroup, pk=pk)
    
    if request.method == "POST":
        form = EmailGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f"Gruppe '{group.name}' wurde aktualisiert.")
            return redirect("messaging:email_group_detail", pk=group.pk)
    else:
        form = EmailGroupForm(instance=group)
    
    return render(request, "messaging/email_group_form.html", {
        "form": form,
        "group": group,
        "title": "Gruppe bearbeiten"
    })


@login_required
@permission_required("messaging.delete_emailgroup", raise_exception=True)
def email_group_delete(request, pk):
    """E-Mail-Gruppe löschen"""
    group = get_object_or_404(EmailGroup, pk=pk)
    
    if request.method == "POST":
        name = group.name
        group.delete()
        messages.success(request, f"Gruppe '{name}' wurde gelöscht.")
        return redirect("messaging:email_group_list")
    
    return render(request, "messaging/email_group_confirm_delete.html", {"group": group})


@login_required
@permission_required("messaging.change_emailgroup", raise_exception=True)
@require_POST
def email_group_add_members(request, pk):
    """Mitglieder zu einer Gruppe hinzufügen"""
    group = get_object_or_404(EmailGroup, pk=pk)
    member_ids = request.POST.getlist("members")
    
    with transaction.atomic():
        for member_id in member_ids:
            EmailGroupMember.objects.get_or_create(
                group=group,
                member_id=member_id,
                defaults={"added_by": request.user}
            )
    
    messages.success(request, f"{len(member_ids)} Mitglieder wurden zur Gruppe hinzugefügt.")
    return redirect("messaging:email_group_detail", pk=group.pk)


@login_required
@permission_required("messaging.change_emailgroup", raise_exception=True)
@require_POST
def email_group_remove_member(request, pk, member_pk):
    """Mitglied aus einer Gruppe entfernen"""
    group = get_object_or_404(EmailGroup, pk=pk)
    membership = get_object_or_404(EmailGroupMember, group=group, member_id=member_pk)
    membership.delete()
    
    messages.success(request, "Mitglied wurde aus der Gruppe entfernt.")
    return redirect("messaging:email_group_detail", pk=group.pk)


# ==================== MASS EMAILS ====================

@login_required
@permission_required("messaging.view_massemail", raise_exception=True)
def mass_email_list(request):
    """Liste aller Massen-E-Mails"""
    emails = MassEmail.objects.select_related("recipient_group", "created_by").all()
    return render(request, "messaging/mass_email_list.html", {"emails": emails})


@login_required
@permission_required("messaging.add_massemail", raise_exception=True)
def mass_email_create(request):
    """Neue Massen-E-Mail erstellen"""
    if request.method == "POST":
        form = MassEmailForm(request.POST)
        if form.is_valid():
            email = form.save(commit=False)
            email.created_by = request.user
            email.save()
            form.save_m2m()
            messages.success(request, "E-Mail-Entwurf wurde gespeichert.")
            return redirect("messaging:mass_email_preview", pk=email.pk)
    else:
        form = MassEmailForm()
    
    return render(request, "messaging/mass_email_form.html", {
        "form": form,
        "title": "Neue Massen-E-Mail"
    })


@login_required
@permission_required("messaging.view_massemail", raise_exception=True)
def mass_email_preview(request, pk):
    """Vorschau einer Massen-E-Mail"""
    email = get_object_or_404(MassEmail, pk=pk)
    
    # Berechne Empfänger
    recipients = get_recipients_for_email(email)
    
    return render(request, "messaging/mass_email_preview.html", {
        "email": email,
        "recipients": recipients[:10],  # Zeige erste 10
        "total_recipients": len(recipients)
    })


@login_required
@permission_required("messaging.change_massemail", raise_exception=True)
def mass_email_edit(request, pk):
    """Massen-E-Mail bearbeiten"""
    email = get_object_or_404(MassEmail, pk=pk)
    
    if email.status != "draft":
        messages.error(request, "Nur Entwürfe können bearbeitet werden.")
        return redirect("messaging:mass_email_preview", pk=email.pk)
    
    if request.method == "POST":
        form = MassEmailForm(request.POST, instance=email)
        if form.is_valid():
            form.save()
            messages.success(request, "E-Mail wurde aktualisiert.")
            return redirect("messaging:mass_email_preview", pk=email.pk)
    else:
        form = MassEmailForm(instance=email)
    
    return render(request, "messaging/mass_email_form.html", {
        "form": form,
        "email": email,
        "title": "E-Mail bearbeiten"
    })


@login_required
@permission_required("messaging.change_massemail", raise_exception=True)
def mass_email_send(request, pk):
    """Massen-E-Mail versenden"""
    email = get_object_or_404(MassEmail, pk=pk)
    
    if email.status != "draft":
        messages.error(request, "Diese E-Mail wurde bereits versendet.")
        return redirect("messaging:mass_email_detail", pk=email.pk)
    
    recipients = get_recipients_for_email(email)
    
    if request.method == "POST":
        form = MassEmailSendForm(request.POST)
        if form.is_valid():
            # Erstelle Email-Logs für alle Empfänger
            with transaction.atomic():
                email.status = "queued"
                email.total_recipients = len(recipients)
                email.sent_by = request.user
                email.save()
                
                for member in recipients:
                    EmailLog.objects.create(
                        mass_email=email,
                        member=member,
                        recipient_email=member.email,
                        tracking_id=str(uuid.uuid4()).replace("-", "")
                    )
            
            # Hier würde normalerweise ein Celery-Task gestartet werden
            # Für jetzt: synchron senden
            from .tasks import send_mass_email_task
            send_mass_email_task.delay(str(email.pk))
            
            messages.success(
                request, 
                f"E-Mail wurde an {len(recipients)} Empfänger in die Warteschlange gestellt."
            )
            return redirect("messaging:mass_email_detail", pk=email.pk)
    else:
        form = MassEmailSendForm()
    
    return render(request, "messaging/mass_email_send.html", {
        "email": email,
        "form": form,
        "recipients": recipients[:10],
        "total_recipients": len(recipients)
    })


@login_required
@permission_required("messaging.view_massemail", raise_exception=True)
def mass_email_detail(request, pk):
    """Detailansicht einer versendeten Massen-E-Mail"""
    email = get_object_or_404(
        MassEmail.objects.prefetch_related("email_logs__member"),
        pk=pk
    )
    
    logs = email.email_logs.all()
    paginator = Paginator(logs, 50)
    page = request.GET.get("page")
    logs_page = paginator.get_page(page)
    
    return render(request, "messaging/mass_email_detail.html", {
        "email": email,
        "logs": logs_page
    })


@login_required
@permission_required("messaging.delete_massemail", raise_exception=True)
def mass_email_delete(request, pk):
    """Massen-E-Mail löschen"""
    email = get_object_or_404(MassEmail, pk=pk)
    
    if request.method == "POST":
        subject = email.subject
        email.delete()
        messages.success(request, f"E-Mail '{subject}' wurde gelöscht.")
        return redirect("messaging:mass_email_list")
    
    return render(request, "messaging/mass_email_confirm_delete.html", {"email": email})


# ==================== HELPER FUNCTIONS ====================

def get_recipients_for_email(email):
    """Holt alle Empfänger für eine Massen-E-Mail"""
    if email.recipient_type == "all":
        return list(Member.objects.filter(
            status="active",
            email__isnull=False
        ).exclude(email=""))
    
    elif email.recipient_type == "group" and email.recipient_group:
        return list(Member.objects.filter(
            email_groups__group=email.recipient_group,
            status="active",
            email__isnull=False
        ).exclude(email=""))
    
    elif email.recipient_type == "individual":
        return list(email.individual_recipients.filter(
            status="active",
            email__isnull=False
        ).exclude(email=""))
    
    return []


# ==================== API ENDPOINTS ====================

@login_required
def api_group_members(request, pk):
    """API: Mitglieder einer Gruppe als JSON"""
    group = get_object_or_404(EmailGroup, pk=pk)
    members = group.members.select_related("member").all()
    
    data = [{
        "id": m.member.id,
        "name": f"{m.member.first_name} {m.member.last_name}",
        "email": m.member.email
    } for m in members]
    
    return JsonResponse({"members": data})


@login_required
def api_email_stats(request, pk):
    """API: Statistik für eine Massen-E-Mail"""
    email = get_object_or_404(MassEmail, pk=pk)
    
    data = {
        "status": email.status,
        "total": email.total_recipients,
        "sent": email.sent_count,
        "failed": email.failed_count,
        "opened": email.opened_count,
        "progress": round((email.sent_count / email.total_recipients * 100), 1) if email.total_recipients > 0 else 0
    }
    
    return JsonResponse(data)


# ==================== TRACKING ====================

def track_email_open(request, tracking_id):
    """Tracking-Pixel für E-Mail-Öffnungen"""
    try:
        log = EmailLog.objects.get(tracking_id=tracking_id)
        if not log.opened_at:
            log.opened_at = timezone.now()
            log.status = "opened"
            log.ip_address = get_client_ip(request)
            log.user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
            log.save()
            
            # Update parent email
            MassEmail.objects.filter(pk=log.mass_email_id).update(
                opened_count=models.F("opened_count") + 1
            )
    except EmailLog.DoesNotExist:
        pass
    
    # Return 1x1 transparent GIF
    return HttpResponse(
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
        content_type="image/gif"
    )


def get_client_ip(request):
    """Holt die Client-IP aus dem Request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
