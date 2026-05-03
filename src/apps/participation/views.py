from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.core.authz import staff_or_board_required
from apps.members.models import Profile

from .forms import ShiftForm, WorkHoursEntryForm
from .models import MemberEngagement, Shift, WorkHours
from .services import sync_profile_work_hours


def _is_staff_or_board(user: User) -> bool:
    return user.is_authenticated and user.role in [User.ROLE_STAFF, User.ROLE_BOARD]


@login_required
def dashboard_view(request):
    profile = Profile.objects.filter(user=request.user).first()
    if profile is None:
        messages.info(request, "Zu deinem Konto ist noch kein Mitgliederprofil vorhanden.")
        return redirect("core:dashboard")
    if request.user.role == User.ROLE_MEMBER and (not profile.is_verified or profile.status != Profile.STATUS_ACTIVE):
        messages.info(request, "Mitwirkung ist erst nach erfolgreicher Verifizierung verfuegbar.")
        return redirect("core:dashboard")
    engagement, _ = MemberEngagement.objects.get_or_create(profile=profile)
    if request.method == "POST":
        form = WorkHoursEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.profile = profile
            entry.approved = False
            entry.save()
            messages.success(request, "Dein Mitwirkungsnachweis wurde gespeichert und wartet auf Freigabe.")
            return redirect("participation:dashboard")
    else:
        form = WorkHoursEntryForm()
    total_hours = profile.work_hours.filter(approved=True).aggregate(total=Sum("hours"))["total"] or 0
    pending_hours = profile.work_hours.filter(approved=False).aggregate(total=Sum("hours"))["total"] or 0
    entries = profile.work_hours.select_related("shift")[:20]
    upcoming_shifts = Shift.objects.filter(starts_at__gte=timezone.now()).order_by("starts_at")[:8]
    return render(
        request,
        "participation/dashboard.html",
        {
            "profile": profile,
            "entries": entries,
            "total_hours": total_hours,
            "pending_hours": pending_hours,
            "engagement": engagement,
            "form": form,
            "upcoming_shifts": upcoming_shifts,
        },
    )


@login_required
def shift_calendar_view(request):
    if request.user.role == User.ROLE_MEMBER:
        profile = Profile.objects.filter(user=request.user).first()
        if profile is None:
            messages.info(request, "Zu deinem Konto ist noch kein Mitgliederprofil vorhanden.")
            return redirect("core:dashboard")
        if not profile.is_verified or profile.status != Profile.STATUS_ACTIVE:
            messages.info(request, "Mitwirkung ist erst nach erfolgreicher Verifizierung verfuegbar.")
            return redirect("core:dashboard")
    shifts = Shift.objects.all()
    return render(
        request,
        "participation/shift_calendar.html",
        {
            "shifts": shifts,
            "can_manage_shifts": _is_staff_or_board(request.user),
        },
    )


@login_required
def shift_detail_view(request, pk: int):
    if request.user.role == User.ROLE_MEMBER:
        profile = Profile.objects.filter(user=request.user).first()
        if profile is None:
            messages.info(request, "Zu deinem Konto ist noch kein Mitgliederprofil vorhanden.")
            return redirect("core:dashboard")
        if not profile.is_verified or profile.status != Profile.STATUS_ACTIVE:
            messages.info(request, "Mitwirkung ist erst nach erfolgreicher Verifizierung verfuegbar.")
            return redirect("core:dashboard")
    shift = get_object_or_404(Shift, pk=pk)
    return render(
        request,
        "participation/shift_detail.html",
        {
            "shift": shift,
        },
    )


@staff_or_board_required(_is_staff_or_board)
def shift_create_view(request):
    if request.method == "POST":
        form = ShiftForm(request.POST)
        if form.is_valid():
            shift = form.save()
            messages.success(request, "Schicht gespeichert.")
            return redirect("participation:shift_detail", pk=shift.pk)
    else:
        form = ShiftForm()
    return render(request, "participation/shift_form.html", {"form": form, "title": "Neue Schicht anlegen"})


@staff_or_board_required(_is_staff_or_board)
def admin_hours_view(request):
    if request.method == "POST":
        entry = get_object_or_404(WorkHours.objects.select_related("profile__user"), id=request.POST.get("entry_id"))
        action = request.POST.get("action")
        if action == "approve":
            entry.approved = True
            entry.save(update_fields=["approved", "updated_at"])
            messages.success(request, "Stundeneintrag freigegeben.")
        elif action == "revoke":
            entry.approved = False
            entry.save(update_fields=["approved", "updated_at"])
            messages.info(request, "Freigabe des Stundeneintrags entfernt.")
        elif action == "delete":
            profile = entry.profile
            entry.delete()
            sync_profile_work_hours(profile)
            messages.warning(request, "Stundeneintrag geloescht.")
        else:
            messages.error(request, "Unbekannte Stundenaktion.")
        return redirect("participation:admin_hours")

    hours = WorkHours.objects.select_related("profile__user", "shift").order_by("-date", "-id")[:100]
    return render(request, "participation/admin_hours.html", {"hours": hours})
