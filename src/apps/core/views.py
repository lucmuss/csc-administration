from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.members.models import Profile
from apps.orders.models import Order
from apps.cultivation.services import CultivationDashboardService


@login_required
def dashboard(request):
    profile = Profile.objects.filter(user=request.user).first()
    recent_orders = Order.objects.filter(member=request.user).order_by("-created_at")[:5]
    cultivation_overview = None
    if request.user.role == "board":
        cultivation_overview = CultivationDashboardService.get_overview()
    return render(
        request,
        "core/dashboard.html",
        {
            "profile": profile,
            "recent_orders": recent_orders,
            "cultivation_overview": cultivation_overview,
        },
    )
