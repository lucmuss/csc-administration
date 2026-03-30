import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from apps.accounts.emails import send_registration_received_email
from apps.accounts.models import User
from apps.finance.models import Invoice

from .forms import MemberRegistrationForm
from .models import Profile


def _is_board(user: User) -> bool:
    return user.is_authenticated and user.role == User.ROLE_BOARD


def _is_staff_or_board(user: User) -> bool:
    return user.is_authenticated and user.role in {User.ROLE_STAFF, User.ROLE_BOARD}


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
def profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, "members/profile.html", {"profile": profile})


@user_passes_test(_is_staff_or_board)
def directory(request):
    query = request.GET.get("q", "").strip()
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

    if action == "verify":
        profile.is_verified = True
        profile.status = Profile.STATUS_ACTIVE
        profile.allocate_member_number()
        profile.save(update_fields=["is_verified", "status", "updated_at"])
        messages.success(request, f"Mitglied {profile.user.email} verifiziert und aktiviert.")
        audit_summary = f"Mitglied {profile.user.email} verifiziert."
    elif action == "activate":
        profile.is_verified = True
        profile.status = Profile.STATUS_ACTIVE
        profile.allocate_member_number()
        profile.save(update_fields=["is_verified", "status", "updated_at"])
        messages.success(request, f"Mitglied {profile.user.email} aktiviert.")
        audit_summary = f"Mitglied {profile.user.email} aktiviert."
    elif action == "reject":
        profile.status = Profile.STATUS_REJECTED
        profile.is_verified = False
        profile.save(update_fields=["status", "is_verified", "updated_at"])
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
        messages.success(request, f"Bestellungen fuer {profile.user.email} wurden freigegeben.")
        audit_summary = f"Bestellsperre fuer {profile.user.email} aufgehoben."
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

    return redirect(request.POST.get("next") or "members:directory")


@user_passes_test(_is_board)
def verify_member(request, profile_id: int):
    request.POST = request.POST.copy()
    request.POST["action"] = "verify"
    return member_action(request, profile_id)
