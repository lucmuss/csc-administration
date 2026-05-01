from datetime import datetime
import csv

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.template.defaultfilters import date as date_filter
from django.utils import timezone

from apps.accounts.models import User
from apps.core.authz import board_required
from apps.members.models import Profile

from .models import ComplianceReport, SuspiciousActivity
from .services import generate_annual_report


def _is_board(user: User) -> bool:
    return user.is_authenticated and user.role == User.ROLE_BOARD


@board_required(_is_board)
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


@board_required(_is_board)
def annual_report(request):
    current_year = timezone.localdate().year
    raw_year = request.GET.get("year", current_year)
    try:
        selected_year = int(raw_year)
    except (TypeError, ValueError):
        selected_year = current_year
        messages.warning(request, "Das Berichtsjahr war ungueltig und wurde auf das aktuelle Jahr zurueckgesetzt.")

    if selected_year < 2024 or selected_year > current_year + 1:
        selected_year = current_year
        messages.warning(request, "Das Berichtsjahr lag ausserhalb des erlaubten Bereichs.")

    report = generate_annual_report(year=selected_year, generated_by=request.user)
    monthly_rows = []
    for row in report.report_data.get("monthly_stats", []):
        month_value = row.get("month")
        month_display = month_value
        if month_value:
            try:
                month_display = date_filter(datetime.fromisoformat(month_value), "F Y")
            except ValueError:
                month_display = month_value
        monthly_rows.append(
            {
                **row,
                "month_display": month_display,
            }
        )

    if request.GET.get("format") == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="cang-jahresmeldung-{selected_year}.csv"'
        writer = csv.writer(response)
        writer.writerow(["Berichtsjahr", selected_year])
        writer.writerow(["Generiert am", report.generated_at.strftime("%d.%m.%Y %H:%M")])
        writer.writerow([])
        writer.writerow(["Kennzahl", "Wert"])
        writer.writerow(["Abgaben", report.total_orders])
        writer.writerow(["Mitglieder", report.total_members])
        writer.writerow(["Gesamtmenge (g)", report.total_grams])
        writer.writerow(["Verdachtsfaelle", report.suspicious_cases])
        writer.writerow([])
        writer.writerow(["Monat", "Abgaben", "Gesamtmenge (g)"])
        for row in monthly_rows:
            writer.writerow([row["month_display"], row["total_orders"], row["total_grams"]])
        return response

    return render(
        request,
        "compliance/annual_report.html",
        {
            "report": report,
            "selected_year": selected_year,
            "monthly_rows": monthly_rows,
        },
    )


@board_required(_is_board)
def suspicious_activity_list(request):
    activities = SuspiciousActivity.objects.select_related("profile__user").order_by("-detected_at")
    return render(request, "compliance/suspicious_activity_list.html", {"activities": activities})


@board_required(_is_board)
def bopst_report(request):
    today = timezone.localdate()
    try:
        month = int(request.GET.get("month", today.month))
        year = int(request.GET.get("year", today.year))
    except (TypeError, ValueError):
        month = today.month
        year = today.year

    report = generate_annual_report(year=year, generated_by=request.user)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="bopst-{year}-{month:02d}.csv"'
    writer = csv.writer(response)
    writer.writerow(["BOPST-Report", f"{month:02d}/{year}"])
    writer.writerow(["Abgaben (Jahr)", report.total_orders])
    writer.writerow(["Mitglieder (Jahr)", report.total_members])
    writer.writerow(["Gesamtmenge (Jahr)", report.total_grams])
    return response


@board_required(_is_board)
def member_export(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="member-export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Mitgliedsnummer", "Status", "Verifiziert", "Monatsverbrauch"])
    for profile in Profile.objects.select_related("user").order_by("member_number"):
        writer.writerow(
            [
                profile.member_number or "",
                profile.status,
                "ja" if profile.is_verified else "nein",
                profile.monthly_used,
            ]
        )
    return response
