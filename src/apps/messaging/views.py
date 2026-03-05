# messaging/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction, models
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Sum, Count, Avg
import uuid

from .models import EmailGroup, EmailGroupMember, MassEmail, EmailLog
from .models import SmsProviderConfig, SmsMessage, SmsTemplate, SmsCostLog
from .forms import (
    EmailGroupForm, EmailGroupMemberForm, MassEmailForm, MassEmailSendForm,
    SmsMessageForm, SmsTemplateForm, SmsSendForm, SmsProviderConfigForm
)
from apps.members.models import Profile


# ==================== DASHBOARD ====================

@login_required
@permission_required("messaging.view_massemail", raise_exception=True)
def messaging_dashboard(request):
    """Messaging Dashboard mit Übersicht"""
    context = {
        "total_groups": EmailGroup.objects.filter(is_active=True).count(),
        "total_emails": MassEmail.objects.exclude(status="draft").count(),
        "total_recipients": MassEmail.objects.aggregate(
            total=Sum("total_recipients")
        )["total"] or 0,
        # SMS Stats
        "total_sms": SmsMessage.objects.exclude(status="draft").count(),
        "sms_this_month": SmsMessage.objects.filter(
            sent_at__year=timezone.now().year,
            sent_at__month=timezone.now().month,
            status="sent"
        ).count(),
        "sms_costs": SmsMessage.objects.filter(
            sent_at__year=timezone.now().year,
            sent_at__month=timezone.now().month
        ).aggregate(total=Sum("cost"))["total"] or 0,
        "active_providers": SmsProviderConfig.objects.filter(is_active=True).count(),
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
    available_members = Profile.objects.filter(status="active").exclude(
        id__in=group.members.values_list("member_id", flat=True)
    ).order_by("user__last_name", "user__first_name")
    
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
                        recipient_email=member.user.email,
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


# ==================== SMS VIEWS ====================

@login_required
@permission_required("messaging.view_smsmessage", raise_exception=True)
def sms_list(request):
    """Liste aller SMS"""
    sms_list = SmsMessage.objects.select_related(
        "recipient_member", "recipient_group", "provider", "created_by"
    ).all()
    
    # Filter
    status_filter = request.GET.get("status")
    if status_filter:
        sms_list = sms_list.filter(status=status_filter)
    
    paginator = Paginator(sms_list, 25)
    page = request.GET.get("page")
    sms_page = paginator.get_page(page)
    
    return render(request, "messaging/sms_list.html", {
        "sms_list": sms_page,
        "status_choices": SmsMessage.STATUS_CHOICES
    })


@login_required
@permission_required("messaging.add_smsmessage", raise_exception=True)
def sms_create(request):
    """Neue SMS erstellen"""
    if request.method == "POST":
        form = SmsMessageForm(request.POST)
        if form.is_valid():
            sms = form.save(commit=False)
            sms.created_by = request.user
            
            # Wenn Template verwendet wird
            template = form.cleaned_data.get("template")
            use_template = form.cleaned_data.get("use_template")
            if use_template and template:
                sms.template_used = template
                # Render Template mit Kontext
                context = {}
                if sms.recipient_member:
                    context = {
                        "first_name": sms.recipient_member.user.first_name,
                        "last_name": sms.recipient_member.user.last_name,
                        "member_number": sms.recipient_member.member_number,
                    }
                sms.content = template.render(context)
            
            sms.save()
            messages.success(request, "SMS-Entwurf wurde gespeichert.")
            return redirect("messaging:sms_preview", pk=sms.pk)
    else:
        form = SmsMessageForm()
    
    return render(request, "messaging/sms_form.html", {
        "form": form,
        "title": "Neue SMS"
    })


@login_required
@permission_required("messaging.view_smsmessage", raise_exception=True)
def sms_preview(request, pk):
    """Vorschau einer SMS"""
    sms = get_object_or_404(SmsMessage, pk=pk)
    
    # Berechne Empfänger
    recipients = get_sms_recipients(sms)
    
    return render(request, "messaging/sms_preview.html", {
        "sms": sms,
        "recipients": recipients[:10],
        "total_recipients": len(recipients)
    })


@login_required
@permission_required("messaging.change_smsmessage", raise_exception=True)
def sms_edit(request, pk):
    """SMS bearbeiten"""
    sms = get_object_or_404(SmsMessage, pk=pk)
    
    if sms.status != "draft":
        messages.error(request, "Nur Entwürfe können bearbeitet werden.")
        return redirect("messaging:sms_preview", pk=sms.pk)
    
    if request.method == "POST":
        form = SmsMessageForm(request.POST, instance=sms)
        if form.is_valid():
            form.save()
            messages.success(request, "SMS wurde aktualisiert.")
            return redirect("messaging:sms_preview", pk=sms.pk)
    else:
        form = SmsMessageForm(instance=sms)
    
    return render(request, "messaging/sms_form.html", {
        "form": form,
        "sms": sms,
        "title": "SMS bearbeiten"
    })


@login_required
@permission_required("messaging.change_smsmessage", raise_exception=True)
def sms_send(request, pk):
    """SMS versenden"""
    sms = get_object_or_404(SmsMessage, pk=pk)
    
    if sms.status != "draft":
        messages.error(request, "Diese SMS wurde bereits versendet.")
        return redirect("messaging:sms_detail", pk=sms.pk)
    
    # Prüfe ob Provider verfügbar
    providers = SmsProviderConfig.objects.filter(is_active=True)
    if not providers.exists():
        messages.error(request, "Kein aktiver SMS-Provider konfiguriert.")
        return redirect("messaging:sms_preview", pk=sms.pk)
    
    recipients = get_sms_recipients(sms)
    
    if request.method == "POST":
        form = SmsSendForm(request.POST)
        if form.is_valid():
            provider = form.cleaned_data["provider"]
            
            if sms.recipient_type == "group":
                # Erstelle einzelne SMS für jedes Gruppenmitglied
                with transaction.atomic():
                    sms.status = "queued"
                    sms.provider = provider
                    sms.sent_by = request.user
                    sms.save()
                    
                    # Für Gruppen: Erstelle individuelle SMS-Einträge
                    for member in recipients:
                        SmsMessage.objects.create(
                            recipient_type="individual",
                            recipient_member=member,
                            recipient_phone=getattr(member, "phone", None) or "",
                            content=sms.content,
                            template_used=sms.template_used,
                            provider=provider,
                            status="queued",
                            created_by=request.user,
                            sent_by=request.user
                        )
            else:
                # Einzelne SMS
                sms.status = "queued"
                sms.provider = provider
                sms.sent_by = request.user
                sms.save()
            
            # Starte Celery Task
            from .tasks import send_sms_task, send_bulk_sms_task
            
            if sms.recipient_type == "group":
                # Sende alle neu erstellten SMS
                new_sms_ids = SmsMessage.objects.filter(
                    content=sms.content,
                    status="queued",
                    created_by=request.user
                ).values_list("id", flat=True)
                send_bulk_sms_task.delay(list(new_sms_ids))
                messages.success(request, f"SMS wurden an {len(recipients)} Empfänger in die Warteschlange gestellt.")
            else:
                send_sms_task.delay(str(sms.pk))
                messages.success(request, "SMS wurde in die Warteschlange gestellt.")
            
            return redirect("messaging:sms_detail", pk=sms.pk)
    else:
        form = SmsSendForm()
    
    return render(request, "messaging/sms_send.html", {
        "sms": sms,
        "form": form,
        "recipients": recipients[:10],
        "total_recipients": len(recipients)
    })


@login_required
@permission_required("messaging.view_smsmessage", raise_exception=True)
def sms_detail(request, pk):
    """Detailansicht einer SMS"""
    sms = get_object_or_404(
        SmsMessage.objects.select_related("recipient_member", "provider", "created_by"),
        pk=pk
    )
    return render(request, "messaging/sms_detail.html", {"sms": sms})


@login_required
@permission_required("messaging.delete_smsmessage", raise_exception=True)
def sms_delete(request, pk):
    """SMS löschen"""
    sms = get_object_or_404(SmsMessage, pk=pk)
    
    if request.method == "POST":
        sms.delete()
        messages.success(request, "SMS wurde gelöscht.")
        return redirect("messaging:sms_list")
    
    return render(request, "messaging/sms_confirm_delete.html", {"sms": sms})


# ==================== SMS TEMPLATES ====================

@login_required
@permission_required("messaging.view_smstemplate", raise_exception=True)
def sms_template_list(request):
    """Liste aller SMS-Vorlagen"""
    templates = SmsTemplate.objects.all()
    return render(request, "messaging/sms_template_list.html", {"templates": templates})


@login_required
@permission_required("messaging.add_smstemplate", raise_exception=True)
def sms_template_create(request):
    """Neue SMS-Vorlage erstellen"""
    if request.method == "POST":
        form = SmsTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, f"Vorlage '{template.name}' wurde erstellt.")
            return redirect("messaging:sms_template_list")
    else:
        form = SmsTemplateForm()
    
    return render(request, "messaging/sms_template_form.html", {
        "form": form,
        "title": "Neue SMS-Vorlage"
    })


@login_required
@permission_required("messaging.change_smstemplate", raise_exception=True)
def sms_template_edit(request, pk):
    """SMS-Vorlage bearbeiten"""
    template = get_object_or_404(SmsTemplate, pk=pk)
    
    if request.method == "POST":
        form = SmsTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vorlage '{template.name}' wurde aktualisiert.")
            return redirect("messaging:sms_template_list")
    else:
        form = SmsTemplateForm(instance=template)
    
    return render(request, "messaging/sms_template_form.html", {
        "form": form,
        "template": template,
        "title": "Vorlage bearbeiten"
    })


@login_required
@permission_required("messaging.delete_smstemplate", raise_exception=True)
def sms_template_delete(request, pk):
    """SMS-Vorlage löschen"""
    template = get_object_or_404(SmsTemplate, pk=pk)
    
    if request.method == "POST":
        name = template.name
        template.delete()
        messages.success(request, f"Vorlage '{name}' wurde gelöscht.")
        return redirect("messaging:sms_template_list")
    
    return render(request, "messaging/sms_template_confirm_delete.html", {"template": template})


# ==================== SMS PROVIDERS ====================

@login_required
@permission_required("messaging.view_smsproviderconfig", raise_exception=True)
def sms_provider_list(request):
    """Liste aller SMS-Provider"""
    providers = SmsProviderConfig.objects.all()
    return render(request, "messaging/sms_provider_list.html", {"providers": providers})


@login_required
@permission_required("messaging.add_smsproviderconfig", raise_exception=True)
def sms_provider_create(request):
    """Neuen SMS-Provider erstellen"""
    if request.method == "POST":
        form = SmsProviderConfigForm(request.POST)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.created_by = request.user
            provider.save()
            messages.success(request, f"Provider '{provider.name}' wurde erstellt.")
            return redirect("messaging:sms_provider_list")
    else:
        form = SmsProviderConfigForm()
    
    return render(request, "messaging/sms_provider_form.html", {
        "form": form,
        "title": "Neuer SMS-Provider"
    })


@login_required
@permission_required("messaging.change_smsproviderconfig", raise_exception=True)
def sms_provider_edit(request, pk):
    """SMS-Provider bearbeiten"""
    provider = get_object_or_404(SmsProviderConfig, pk=pk)
    
    if request.method == "POST":
        form = SmsProviderConfigForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, f"Provider '{provider.name}' wurde aktualisiert.")
            return redirect("messaging:sms_provider_list")
    else:
        form = SmsProviderConfigForm(instance=provider)
    
    return render(request, "messaging/sms_provider_form.html", {
        "form": form,
        "provider": provider,
        "title": "Provider bearbeiten"
    })


@login_required
@permission_required("messaging.delete_smsproviderconfig", raise_exception=True)
def sms_provider_delete(request, pk):
    """SMS-Provider löschen"""
    provider = get_object_or_404(SmsProviderConfig, pk=pk)
    
    if request.method == "POST":
        name = provider.name
        provider.delete()
        messages.success(request, f"Provider '{name}' wurde gelöscht.")
        return redirect("messaging:sms_provider_list")
    
    return render(request, "messaging/sms_provider_confirm_delete.html", {"provider": provider})


# ==================== SMS STATISTICS ====================

@login_required
@permission_required("messaging.view_smsmessage", raise_exception=True)
def sms_stats(request):
    """SMS-Statistiken"""
    from django.db.models import Sum, Count, Avg
    
    # Gesamtstatistiken
    total_stats = SmsMessage.objects.aggregate(
        total=Count("id"),
        sent=Count("id", filter=models.Q(status="sent")),
        failed=Count("id", filter=models.Q(status="failed")),
        total_cost=Sum("cost")
    )
    
    # Monatliche Statistiken
    monthly_stats = SmsMessage.objects.filter(
        status="sent"
    ).extra(
        select={"month": "strftime('%Y-%m', sent_at)"}
    if "sqlite" in settings.DATABASES["default"]["ENGINE"] else
        {"month": "TO_CHAR(sent_at, 'YYYY-MM')"}
    ).values("month").annotate(
        count=Count("id"),
        cost=Sum("cost")
    ).order_by("-month")[:12]
    
    # Provider-Statistiken
    provider_stats = SmsMessage.objects.filter(
        status="sent"
    ).values("provider__name").annotate(
        count=Count("id"),
        cost=Sum("cost")
    ).order_by("-count")
    
    # Status-Verteilung
    status_stats = SmsMessage.objects.values("status").annotate(
        count=Count("id")
    ).order_by("-count")
    
    context = {
        "total_stats": total_stats,
        "monthly_stats": monthly_stats,
        "provider_stats": provider_stats,
        "status_stats": status_stats,
    }
    return render(request, "messaging/sms_stats.html", context)


# ==================== HELPER FUNCTIONS ====================

def get_recipients_for_email(email):
    """Holt alle Empfänger für eine Massen-E-Mail"""
    if email.recipient_type == "all":
        return list(Profile.objects.filter(
            status="active",
            user__email__isnull=False
        ).exclude(user__email=""))
    
    elif email.recipient_type == "group" and email.recipient_group:
        return list(Profile.objects.filter(
            email_groups__group=email.recipient_group,
            status="active",
            user__email__isnull=False
        ).exclude(user__email=""))
    
    elif email.recipient_type == "individual":
        return list(email.individual_recipients.filter(
            status="active",
            user__email__isnull=False
        ).exclude(user__email=""))
    
    return []


def get_sms_recipients(sms):
    """Holt alle Empfänger für eine SMS"""
    if sms.recipient_type == "individual":
        if sms.recipient_member:
            return [sms.recipient_member]
        return []
    
    elif sms.recipient_type == "group" and sms.recipient_group:
        return list(Profile.objects.filter(
            email_groups__group=sms.recipient_group,
            status="active"
        ).distinct())
    
    return []


# ==================== API ENDPOINTS ====================

@login_required
def api_group_members(request, pk):
    """API: Mitglieder einer Gruppe als JSON"""
    group = get_object_or_404(EmailGroup, pk=pk)
    members = group.members.select_related("member").all()
    
    data = [{
        "id": m.member.id,
        "name": f"{m.member.user.first_name} {m.member.user.last_name}",
        "email": m.member.user.email
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


@login_required
def api_sms_character_count(request):
    """API: Zeichenzähler für SMS"""
    text = request.GET.get("text", "")
    chars = len(text)
    sms_count = 1 if chars <= 160 else (chars + 153 - 1) // 153
    
    return JsonResponse({
        "characters": chars,
        "sms_count": sms_count,
        "remaining": 160 if sms_count == 1 else (sms_count * 153) - chars
    })


@login_required
def api_render_sms_template(request):
    """API: Rendert eine SMS-Vorlage mit Beispieldaten"""
    template_id = request.GET.get("template_id")
    
    try:
        template = SmsTemplate.objects.get(pk=template_id)
        # Beispiel-Kontext
        context = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "member_number": "123456"
        }
        rendered = template.render(context)
        
        return JsonResponse({
            "success": True,
            "rendered": rendered,
            "characters": len(rendered),
            "sms_count": 1 if len(rendered) <= 160 else (len(rendered) + 153 - 1) // 153
        })
    except SmsTemplate.DoesNotExist:
        return JsonResponse({"success": False, "error": "Template nicht gefunden"})


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
