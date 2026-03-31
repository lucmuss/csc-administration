import csv
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from apps.accounts.emails import (
    send_membership_documents_email,
    send_membership_status_email,
    send_registration_received_email,
)
from apps.accounts.models import User
from apps.finance.models import Invoice
from apps.messaging.services import sync_member_messaging_preferences
from apps.orders.models import Order

from .forms import MemberOnboardingForm, MemberProfileEditForm, MemberRegistrationForm
from .models import Profile

_SEARCH_SANITIZE_RE = re.compile(r"[^0-9A-Za-zÄÖÜäöüß@._+\-\s]")


def _is_board(user: User) -> bool:
    return user.is_authenticated and user.role == User.ROLE_BOARD


def _is_staff_or_board(user: User) -> bool:
    return user.is_authenticated and user.role in {User.ROLE_STAFF, User.ROLE_BOARD}


def _sanitize_search_query(raw: str) -> str:
    compact = " ".join(raw.split()).strip()
    sanitized = _SEARCH_SANITIZE_RE.sub("", compact)
    return sanitized[:80].strip()


def _normalize_directory_query(request):
    raw_query = request.GET.get("q", "")
    sanitized_query = _sanitize_search_query(raw_query)
    if raw_query.strip() == sanitized_query:
        return sanitized_query, None
    params = request.GET.copy()
    if sanitized_query:
        params["q"] = sanitized_query
    else:
        params.pop("q", None)
    query_string = params.urlencode()
    target = request.path
    if query_string:
        target = f"{target}?{query_string}"
    return sanitized_query, redirect(target)


def register(request):
    if request.method == "POST":
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_registration_received_email(
                user,
                request,
                is_bootstrap=user.role == User.ROLE_BOARD,
            )
            if user.role == User.ROLE_BOARD:
                messages.success(
                    request,
                    "Erster Systemzugang angelegt. Dieser Account wurde als Vorstand freigeschaltet.",
                )
            else:
                messages.success(
                    request,
                    "Registrierung erfolgreich. Freischaltung folgt nach Verifizierung.",
                )
            return redirect("accounts:login")
    else:
        form = MemberRegistrationForm()
    return render(request, "members/register.html", {"form": form, "is_bootstrap": not User.objects.exists()})


@login_required
def onboarding_view(request):
    profile = get_object_or_404(Profile.objects.select_related("user"), user=request.user)
    engagement = getattr(profile, "engagement", None)
    if profile.onboarding_complete:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = MemberOnboardingForm(request.POST, profile=profile)
        if form.is_valid():
            form.save()
            if request.user.role == User.ROLE_MEMBER:
                send_membership_documents_email(profile, request)
            messages.success(request, "Deine Registrierungsdaten wurden vervollstaendigt.")
            return redirect("core:dashboard")
    else:
        form = MemberOnboardingForm(profile=profile)

    return render(
        request,
        "members/onboarding.html",
        {
            "form": form,
            "profile": profile,
            "engagement": engagement,
        },
    )


@login_required
def profile_view(request):
    profile = get_object_or_404(Profile.objects.select_related("user"), user=request.user)
    if request.method == "POST":
        form = MemberProfileEditForm(request.POST, profile=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Deine Profildaten wurden aktualisiert.")
            return redirect("members:profile")
    else:
        form = MemberProfileEditForm(profile=profile)
    recent_orders = Order.objects.filter(member=request.user).prefetch_related("items__strain").order_by("-created_at")[:8]
    invoices = profile.invoices.order_by("-created_at")[:8]
    payments = profile.payments.select_related("invoice").order_by("-created_at")[:8]
    return render(
        request,
        "members/profile.html",
        {
            "profile": profile,
            "recent_orders": recent_orders,
            "invoices": invoices,
            "payments": payments,
            "is_admin_view": False,
            "can_manage": False,
            "can_view_sensitive_finance": True,
            "show_full_bic": True,
            "show_order_history": True,
            "show_private_profile_details": True,
            "profile_form": form,
            "show_public_directory_link": True,
            "show_profile_edit_callout": True,
        },
    )


@login_required
def member_detail(request, profile_id: int):
    profile = get_object_or_404(Profile.objects.select_related("user"), id=profile_id)
    viewer = request.user
    is_admin_view = viewer.role in {User.ROLE_STAFF, User.ROLE_BOARD}
    is_self_view = viewer.id == profile.user_id
    if viewer.role == User.ROLE_MEMBER and not is_self_view:
        if profile.status not in {Profile.STATUS_ACTIVE, Profile.STATUS_VERIFIED}:
            messages.error(request, "Dieses Mitgliederprofil ist aktuell nicht freigegeben.")
            return redirect("members:directory")

    recent_orders = (
        Order.objects.filter(member=profile.user).prefetch_related("items__strain").order_by("-created_at")[:12]
        if is_admin_view or is_self_view
        else []
    )
    invoices = profile.invoices.order_by("-created_at")[:12] if is_admin_view or is_self_view else []
    payments = profile.payments.select_related("invoice").order_by("-created_at")[:12] if is_admin_view or is_self_view else []
    return render(
        request,
        "members/profile.html",
        {
            "profile": profile,
            "recent_orders": recent_orders,
            "invoices": invoices,
            "payments": payments,
            "is_admin_view": is_admin_view,
            "can_manage": viewer.role == User.ROLE_BOARD,
            "can_view_sensitive_finance": is_self_view or viewer.role == User.ROLE_BOARD,
            "show_full_bic": is_self_view or viewer.role == User.ROLE_BOARD,
            "show_order_history": is_admin_view or is_self_view,
            "show_private_profile_details": is_admin_view or is_self_view,
            "profile_form": None,
            "show_public_directory_link": True,
            "show_profile_edit_callout": False,
        },
    )


@login_required
def directory(request):
    _, redirect_response = _normalize_directory_query(request)
    if redirect_response:
        return redirect_response
    if request.user.role in {User.ROLE_STAFF, User.ROLE_BOARD}:
        return _staff_directory(request)
    return _member_directory(request)


def _staff_directory(request):
    query = _sanitize_search_query(request.GET.get("q", ""))
    status_filter = request.GET.get("status", "").strip()
    locked_filter = request.GET.get("locked", "").strip()

    profiles = (
        Profile.objects.select_related("user")
        .annotate(
            open_invoice_count=Count(
                "invoices",
                filter=Q(invoices__status=Invoice.STATUS_OPEN),
                distinct=True,
            ),
            suspicious_count=Count(
                "suspicious_activities",
                filter=Q(suspicious_activities__is_reported=False),
                distinct=True,
            ),
        )
        .order_by("status", "member_number", "user__last_name", "user__first_name")
    )

    if query:
        query_filter = (
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
        )
        if query.isdigit():
            query_filter |= Q(member_number=int(query))
        profiles = profiles.filter(query_filter)

    if status_filter:
        profiles = profiles.filter(status=status_filter)

    if locked_filter == "yes":
        profiles = profiles.filter(is_locked_for_orders=True)
    elif locked_filter == "no":
        profiles = profiles.filter(is_locked_for_orders=False)

    paginator = Paginator(profiles, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "members/directory.html",
        {
            "page_obj": page_obj,
            "status_choices": Profile.STATUS_CHOICES,
            "filters": {
                "q": query,
                "status": status_filter,
                "locked": locked_filter,
            },
            "can_manage": request.user.role == User.ROLE_BOARD,
        },
    )


def _member_directory(request):
    query = _sanitize_search_query(request.GET.get("q", ""))
    profiles = (
        Profile.objects.select_related("user")
        .filter(status__in=[Profile.STATUS_ACTIVE, Profile.STATUS_VERIFIED])
        .exclude(user=request.user)
        .order_by("user__first_name", "user__last_name")
    )
    if query:
        profiles = profiles.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
        )
    paginator = Paginator(profiles, 24)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "members/directory.html",
        {
            "page_obj": page_obj,
            "status_choices": Profile.STATUS_CHOICES,
            "filters": {"q": query, "status": "", "locked": ""},
            "can_manage": False,
            "is_member_directory": True,
        },
    )


@user_passes_test(_is_staff_or_board)
def export_members_csv(request):
    profiles = Profile.objects.select_related("user").order_by("member_number", "user__last_name")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="csc-members.csv"'

    writer = csv.writer(response, delimiter=";")
    writer.writerow(
        [
            "Mitgliedsnummer",
            "Status",
            "Verifiziert",
            "Vorname",
            "Nachname",
            "E-Mail",
            "Rolle",
            "Guthaben",
            "Tagesverbrauch",
            "Monatsverbrauch",
            "Bestellungen gesperrt",
        ]
    )
    for profile in profiles:
        writer.writerow(
            [
                profile.member_number or "",
                profile.get_status_display(),
                "Ja" if profile.is_verified else "Nein",
                profile.user.first_name,
                profile.user.last_name,
                profile.user.email,
                profile.user.get_role_display(),
                profile.balance,
                profile.daily_used,
                profile.monthly_used,
                "Ja" if profile.is_locked_for_orders else "Nein",
            ]
        )
    return response


@user_passes_test(_is_board)
def member_action(request, profile_id: int):
    profile = get_object_or_404(Profile.objects.select_related("user"), id=profile_id)
    action = request.POST.get("action")
    audit_summary = ""
    next_target = request.POST.get("next") or "members:directory"

    sensitive_actions = {"verify", "activate", "reject", "lock_orders", "unlock_orders", "delete_member"}
    if action in sensitive_actions and request.POST.get("confirm") not in {"yes", "no"}:
        return render(
            request,
            "members/action_confirm.html",
            {
                "profile": profile,
                "action": action,
                "next": next_target,
            },
        )
    if request.POST.get("confirm") == "no":
        messages.info(request, "Die Mitgliederaktion wurde abgebrochen.")
        return redirect(next_target)

    if action == "verify":
        profile.is_verified = True
        profile.status = Profile.STATUS_ACTIVE
        profile.allocate_member_number()
        profile.save(update_fields=["is_verified", "status", "updated_at"])
        sync_member_messaging_preferences(profile)
        send_membership_status_email(
            profile.user,
            request,
            status_title="Mitgliedschaft freigeschaltet",
            message="Dein Account wurde geprueft und fuer den Clubbetrieb freigeschaltet.",
        )
        messages.success(request, f"Mitglied {profile.user.email} verifiziert und aktiviert.")
        audit_summary = f"Mitglied {profile.user.email} verifiziert."
    elif action == "activate":
        profile.is_verified = True
        profile.status = Profile.STATUS_ACTIVE
        profile.allocate_member_number()
        profile.save(update_fields=["is_verified", "status", "updated_at"])
        sync_member_messaging_preferences(profile)
        send_membership_status_email(
            profile.user,
            request,
            status_title="Mitgliedschaft aktiviert",
            message="Dein Zugang wurde aktiviert. Du kannst dich jetzt regulaer anmelden.",
        )
        messages.success(request, f"Mitglied {profile.user.email} aktiviert.")
        audit_summary = f"Mitglied {profile.user.email} aktiviert."
    elif action == "reject":
        profile.status = Profile.STATUS_REJECTED
        profile.is_verified = False
        profile.save(update_fields=["status", "is_verified", "updated_at"])
        send_membership_status_email(
            profile.user,
            request,
            status_title="Mitgliedschaft abgelehnt",
            message="Deine Registrierung wurde aktuell nicht freigegeben. Bitte melde dich beim Club, falls Rueckfragen offen sind.",
        )
        messages.warning(request, f"Mitglied {profile.user.email} wurde abgelehnt.")
        audit_summary = f"Mitglied {profile.user.email} abgelehnt."
    elif action == "lock_orders":
        profile.is_locked_for_orders = True
        profile.save(update_fields=["is_locked_for_orders", "updated_at"])
        messages.warning(request, f"Bestellungen fuer {profile.user.email} wurden gesperrt.")
        audit_summary = f"Bestellsperre fuer {profile.user.email} aktiviert."
    elif action == "unlock_orders":
        profile.is_locked_for_orders = False
        profile.save(update_fields=["is_locked_for_orders", "updated_at"])
        send_membership_status_email(
            profile.user,
            request,
            status_title="Bestellsperre aufgehoben",
            message="Deine Bestellungen wurden wieder freigegeben. Du kannst den Shop wieder normal nutzen.",
        )
        messages.success(request, f"Bestellungen fuer {profile.user.email} wurden freigegeben.")
        audit_summary = f"Bestellsperre fuer {profile.user.email} aufgehoben."
    elif action == "delete_member":
        if profile.user_id == request.user.id:
            messages.error(request, "Der eigene Admin-Zugang kann hier nicht geloescht werden.")
            return redirect(next_target)
        user_email = profile.user.email
        from apps.governance.services import record_audit_event

        record_audit_event(
            actor=request.user,
            domain="members",
            action="deleted",
            target=profile,
            summary=f"Mitglied {user_email} wurde geloescht.",
            metadata={"status": profile.status},
            request=request,
        )
        profile.user.delete()
        messages.warning(request, f"Mitglied {user_email} wurde geloescht.")
        return redirect("members:directory")
    else:
        messages.error(request, "Unbekannte Aktion.")

    if audit_summary:
        from apps.governance.services import record_audit_event

        record_audit_event(
            actor=request.user,
            domain="members",
            action=action,
            target=profile,
            summary=audit_summary,
            metadata={"status": profile.status, "locked_for_orders": profile.is_locked_for_orders},
            request=request,
        )

    return redirect(next_target)


@user_passes_test(_is_board)
def verify_member(request, profile_id: int):
    request.POST = request.POST.copy()
    request.POST["action"] = "verify"
    return member_action(request, profile_id)
