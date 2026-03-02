from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.models import User

from .models import ComplianceReport, SuspiciousActivity
from .services import generate_annual_report


def _is_board(user: User) -> bool:
    return user.is_authenticated and user.role == User.ROLE_BOARD


@user_passes_test(_is_board)
def dashboard(request):
    year = timezone.localdate().year
    latest_report = ComplianceReport.objects.order_by("-year").first()
    suspicious_open = SuspiciousActivity.objects.filter(is_reported=False).select_related("profile__user")[:20]

    return render(
        request,
        "compliance/dashboard.html",
        {
            "year": year,
            "latest_report": latest_report,
            "suspicious_open": suspicious_open,
        },
    )


@user_passes_test(_is_board)
def annual_report(request):
    selected_year = int(request.GET.get("year", timezone.localdate().year))
    report = generate_annual_report(year=selected_year, generated_by=request.user)

    return render(
        request,
        "compliance/annual_report.html",
        {
            "report": report,
            "selected_year": selected_year,
        },
    )


@user_passes_test(_is_board)
def suspicious_activity_list(request):
    activities = SuspiciousActivity.objects.select_related("profile__user").order_by("-detected_at")
    return render(request, "compliance/suspicious_activity_list.html", {"activities": activities})
