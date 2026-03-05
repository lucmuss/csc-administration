# messaging/tasks.py
from celery import shared_task
from django.core.mail import send_mail, get_connection
from django.template import Template, Context
from django.utils import timezone
from django.conf import settings
import time

from .models import MassEmail, EmailLog


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
                "first_name": log.member.first_name,
                "last_name": log.member.last_name,
                "email": log.member.email,
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
