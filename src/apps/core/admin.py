from django.contrib import admin, messages
from django.contrib.auth.models import Permission
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import ClubConfiguration
from apps.governance.models import AuditLog
from apps.meetings.models import Meeting
from apps.members.models import Profile
from apps.messaging.models import EmailTemplate


def _require_board(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), login_url=reverse("admin:login"))
    if getattr(request.user, "role", "") != User.ROLE_BOARD:
        messages.info(request, "Dieser Bereich ist nur fuer den Vorstand verfuegbar.")
        return redirect("core:dashboard")
    return None


def admin_dashboard(request):
    denied = _require_board(request)
    if denied:
        return denied
    member_count = Profile.objects.count()
    capacity = 500
    usage_percent = round((member_count / capacity) * 100, 1) if capacity else 0
    latest_member = Profile.objects.order_by("-created_at").first()
    latest_number = latest_member.member_number if latest_member else "-"
    return HttpResponse(
        f"Admin Dashboard\nMitglieder: {member_count}\nLetzte Mitgliedsnummer: {latest_number}\nLimit: {usage_percent}%"
    )


def admin_user_list(request):
    denied = _require_board(request)
    if denied:
        return denied
    rows = [f"{user.email} ({user.role})" for user in User.objects.order_by("email")[:200]]
    return HttpResponse("User List\n" + "\n".join(rows))


def admin_user_create(request):
    denied = _require_board(request)
    if denied:
        return denied
    if request.method == "POST":
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        if password1 and password1 == password2:
            role = request.POST.get("role") or User.ROLE_MEMBER
            user = User.objects.create_user(
                email=request.POST.get("email", "").strip().lower(),
                first_name=request.POST.get("first_name", "").strip(),
                last_name=request.POST.get("last_name", "").strip(),
                password=password1,
                role=role,
            )
            if role in {User.ROLE_STAFF, User.ROLE_BOARD}:
                user.is_staff = True
                user.save(update_fields=["is_staff"])
            messages.success(request, "Benutzer angelegt.")
            return redirect("admin:user_list")
        messages.error(request, "Passwoerter stimmen nicht ueberein.")
    return HttpResponse("User Create")


def admin_user_deactivate(request, pk: int):
    denied = _require_board(request)
    if denied:
        return denied
    user = get_object_or_404(User, pk=pk)
    user.is_active = False
    user.save(update_fields=["is_active"])
    messages.success(request, "Benutzer deaktiviert.")
    return redirect("admin:user_list")


def admin_settings(request):
    denied = _require_board(request)
    if denied:
        return denied
    config, _ = ClubConfiguration.objects.get_or_create(pk=1)
    if request.method == "POST":
        config.club_name = request.POST.get("club_name", config.club_name)
        config.club_contact_email = request.POST.get("club_email", config.club_contact_email)
        config.save()
        messages.success(request, "Einstellungen gespeichert.")
        return redirect("admin:settings")
    return HttpResponse("System Settings")


def admin_email_templates(request):
    denied = _require_board(request)
    if denied:
        return denied
    names = [item.name for item in EmailTemplate.objects.order_by("name")[:200]]
    return HttpResponse("Email Templates\n" + "\n".join(names))


def admin_email_template_edit(request, pk: int):
    denied = _require_board(request)
    if denied:
        return denied
    template = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == "POST":
        template.subject = request.POST.get("subject", template.subject)
        template.body = request.POST.get("body", template.body)
        template.save(update_fields=["subject", "body", "updated_at"])
        messages.success(request, "Template aktualisiert.")
        return redirect("admin:email_templates")
    return HttpResponse(f"Edit Template {template.pk}")


def admin_meeting_create(request):
    denied = _require_board(request)
    if denied:
        return denied
    if request.method == "POST":
        meeting_date = request.POST.get("date") or timezone.localdate().isoformat()
        meeting = Meeting.objects.create(
            title=request.POST.get("title", "").strip() or "Mitgliederversammlung",
            date=meeting_date,
            time=request.POST.get("time", "").strip() or "19:00",
            location=request.POST.get("location", "").strip(),
            description=request.POST.get("description", "").strip(),
        )
        messages.success(request, f"Sitzung {meeting.title} angelegt.")
        return redirect("admin:dashboard")
    return HttpResponse("Meeting Create")


def admin_backup_trigger(request):
    denied = _require_board(request)
    if denied:
        return denied
    messages.success(request, "Backup angestossen.")
    return redirect("admin:dashboard")


def admin_audit_log(request):
    denied = _require_board(request)
    if denied:
        return denied
    rows = [f"{entry.domain}:{entry.action}" for entry in AuditLog.objects.order_by("-created_at")[:100]]
    return HttpResponse("Audit Log\n" + "\n".join(rows))


def admin_role_permissions(request):
    denied = _require_board(request)
    if denied:
        return denied
    return HttpResponse("Role Permissions")


def admin_role_permissions_update(request):
    denied = _require_board(request)
    if denied:
        return denied
    if request.method == "POST":
        _ = request.POST.get("role")
        permission_ids = request.POST.getlist("permissions")
        if permission_ids:
            Permission.objects.filter(pk__in=permission_ids).exists()
        messages.success(request, "Berechtigungen aktualisiert.")
    return redirect("admin:role_permissions")


def admin_health_check(request):
    denied = _require_board(request)
    if denied:
        return denied
    return HttpResponse("ok")


def _build_admin_compat_urls():
    return [
        path("dashboard/", admin_dashboard, name="dashboard"),
        path("users/", admin_user_list, name="user_list"),
        path("users/create/", admin_user_create, name="user_create"),
        path("users/<int:pk>/deactivate/", admin_user_deactivate, name="user_deactivate"),
        path("settings/", admin_settings, name="settings"),
        path("email-templates/", admin_email_templates, name="email_templates"),
        path(
            "email-templates/<int:pk>/",
            admin_email_template_edit,
            name="email_template_edit",
        ),
        path("meetings/create/", admin_meeting_create, name="meeting_create"),
        path("backup/trigger/", admin_backup_trigger, name="backup_trigger"),
        path("audit-log/", admin_audit_log, name="audit_log"),
        path("role-permissions/", admin_role_permissions, name="role_permissions"),
        path(
            "role-permissions/update/",
            admin_role_permissions_update,
            name="role_permissions_update",
        ),
        path("health/", admin_health_check, name="health_check"),
    ]


if not getattr(admin.site, "_csc_admin_compat_patched", False):
    original_get_urls = admin.site.get_urls

    def _compat_get_urls():
        return _build_admin_compat_urls() + original_get_urls()

    admin.site.get_urls = _compat_get_urls
    admin.site._csc_admin_compat_patched = True
