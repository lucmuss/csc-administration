from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render

from apps.accounts.models import User
from apps.members.models import Profile

from .models import MemberEngagement, Shift, WorkHours


def _is_staff_or_board(user: User) -> bool:
    return user.is_authenticated and user.role in [User.ROLE_STAFF, User.ROLE_BOARD]


@login_required
def dashboard_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    engagement, _ = MemberEngagement.objects.get_or_create(profile=profile)
    total_hours = profile.work_hours.filter(approved=True).aggregate(total=Sum("hours"))["total"] or 0
    entries = profile.work_hours.select_related("shift")[:20]
    return render(
        request,
        "participation/dashboard.html",
        {
            "profile": profile,
            "entries": entries,
            "total_hours": total_hours,
            "engagement": engagement,
        },
    )


@login_required
def shift_calendar_view(request):
    shifts = Shift.objects.all()
    return render(request, "participation/shift_calendar.html", {"shifts": shifts})


@user_passes_test(_is_staff_or_board)
def admin_hours_view(request):
    hours = WorkHours.objects.select_related("profile__user", "shift").order_by("-date", "-id")[:100]
    return render(request, "participation/admin_hours.html", {"hours": hours})
