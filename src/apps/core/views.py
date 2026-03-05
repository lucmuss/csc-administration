from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.members.models import Profile
from apps.orders.models import Order


@login_required
def dashboard(request):
    profile = Profile.objects.filter(user=request.user).first()
    recent_orders = Order.objects.filter(member=request.user).order_by("-created_at")[:5]
    return render(
        request,
        "core/dashboard.html",
        {
            "profile": profile,
            "recent_orders": recent_orders,
        },
    )
