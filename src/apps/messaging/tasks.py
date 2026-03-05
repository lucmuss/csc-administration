# messaging/tasks.py
from celery import shared_task
from django.core.mail import send_mail, get_connection
from django.template import Template, Context
from django.utils import timezone
from django.conf import settings
import time

from .models import MassEmail, EmailLog, SmsMessage, SmsCostLog
from .services import send_sms_message


@shared_task
def send_mass_email_task(email_id):
    """Sendet eine Massen-E-Mail an alle Empfänger"""
    try:
        email = MassEmail.objects.get(pk=email_id)
    except MassEmail.DoesNotExist:
        return {"error": "Email not found"}
    
    if email.status not in ["queued", "draft"]:
        return {"error": f"Invalid status: {email.status}"}
    
    email.status = "sending"
    email.save()
    
    # Hole alle ausstehenden Logs
    pending_logs = EmailLog.objects.filter(
        mass_email=email,
        status__in=["pending", "failed"]
    ).select_related("member")
    
    sent = 0
    failed = 0
    
    for log in pending_logs:
        try:
            # Personalisiere Inhalt
            context = {
                "first_name": log.member.user.first_name,
                "last_name": log.member.user.last_name,
                "email": log.member.user.email,
                "member_number": log.member.member_number,
            }
            
            template = Template(email.content_html)
            personalized_html = template.render(Context(context))
            
            # Füge Tracking-Pixel hinzu
            tracking_pixel = f'<img src="{settings.SITE_URL}/messaging/track/{log.tracking_id}.gif" width="1" height="1" alt="" />'
            personalized_html += tracking_pixel
            
            # Sende E-Mail
            send_mail(
                subject=email.subject,
                message=email.content,  # Plain text
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[log.recipient_email],
                html_message=personalized_html,
                fail_silently=False,
            )
            
            log.status = "sent"
            log.sent_at = timezone.now()
            log.save()
            sent += 1
            
            # Kleine Pause um Rate-Limits zu vermeiden
            time.sleep(0.1)
            
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)[:500]
            log.save()
            failed += 1
    
    # Update Email-Status
    email.sent_count += sent
    email.failed_count += failed
    
    if email.failed_count == 0:
        email.status = "sent"
        email.sent_at = timezone.now()
    elif email.sent_count > 0:
        email.status = "sent"  # Teilweise erfolgreich
    else:
        email.status = "failed"
    
    email.save()
    
    return {
        "email_id": str(email_id),
        "sent": sent,
        "failed": failed,
        "status": email.status
    }


# ==================== SMS TASKS ====================

@shared_task
def send_sms_task(sms_id):
    """Sendet eine einzelne SMS"""
    try:
        sms = SmsMessage.objects.get(pk=sms_id)
    except SmsMessage.DoesNotExist:
        return {"error": "SMS not found"}
    
    if sms.status not in ["queued", "draft"]:
        return {"error": f"Invalid status: {sms.status}"}
    
    sms.status = "sending"
    sms.save()
    
    success = send_sms_message(sms)
    
    return {
        "sms_id": str(sms_id),
        "success": success,
        "status": sms.status,
        "external_id": sms.external_id
    }


@shared_task
def send_bulk_sms_task(sms_ids, group_id=None):
    """Sendet mehrere SMS (z.B. an eine Gruppe)"""
    results = []
    
    for sms_id in sms_ids:
        result = send_sms_task.delay(sms_id)
        results.append(str(sms_id))
    
    return {
        "queued": len(results),
        "sms_ids": results
    }


@shared_task
def update_sms_cost_log():
    """Aktualisiert die monatlichen SMS-Kosten"""
    from django.db.models import Sum, Count
    
    current_month = timezone.now().strftime("%Y-%m")
    
    # Aggregiere Kosten für den aktuellen Monat
    stats = SmsMessage.objects.filter(
        sent_at__year=timezone.now().year,
        sent_at__month=timezone.now().month,
        status="sent"
    ).aggregate(
        total_messages=Count("id"),
        total_cost=Sum("cost")
    )
    
    # Provider-Breakdown
    provider_stats = SmsMessage.objects.filter(
        sent_at__year=timezone.now().year,
        sent_at__month=timezone.now().month,
        status="sent"
    ).values("provider__name").annotate(
        count=Count("id"),
        cost=Sum("cost")
    )
    
    provider_breakdown = {
        stat["provider__name"]: {
            "count": stat["count"],
            "cost": float(stat["cost"]) if stat["cost"] else 0
        }
        for stat in provider_stats
    }
    
    # Update oder erstelle Log-Eintrag
    SmsCostLog.objects.update_or_create(
        month=current_month,
        defaults={
            "total_messages": stats["total_messages"] or 0,
            "total_cost": stats["total_cost"] or 0,
            "provider_breakdown": provider_breakdown
        }
    )
    
    return {
        "month": current_month,
        "total_messages": stats["total_messages"] or 0,
        "total_cost": float(stats["total_cost"]) if stats["total_cost"] else 0
    }
