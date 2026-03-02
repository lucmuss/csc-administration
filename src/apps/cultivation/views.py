from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from .models import Cutting, MotherPlant, Plant
from .services import CultivationDashboardService, GrowLogService, HarvestService


@login_required
def dashboard(request):
    overview = CultivationDashboardService.get_overview()
    return render(request, "cultivation/dashboard.html", overview)


@login_required
def mother_plant_list(request):
    mothers = MotherPlant.objects.select_related("strain").all()
    return render(request, "cultivation/mother_plant_list.html", {"mother_plants": mothers})


@login_required
def cutting_list(request):
    cuttings = Cutting.objects.select_related("mother_plant__strain").all()
    return render(request, "cultivation/cutting_list.html", {"cuttings": cuttings})


@login_required
def plant_detail(request, plant_id):
    plant = get_object_or_404(Plant.objects.select_related("cutting__mother_plant__strain"), pk=plant_id)

    if request.method == "POST" and request.POST.get("action") == "add_log":
        try:
            GrowLogService.add_entry(
                plant=plant,
                entry_date=date.fromisoformat(request.POST.get("date")),
                activity_type=request.POST.get("activity_type"),
                notes=request.POST.get("notes", ""),
                nutrients=request.POST.get("nutrients", ""),
            )
            messages.success(request, "Growtagebuch-Eintrag gespeichert")
            return redirect("cultivation:plant_detail", plant_id=plant.id)
        except Exception as exc:
            messages.error(request, str(exc))

    logs = plant.growth_logs.all()
    return render(request, "cultivation/plant_detail.html", {"plant": plant, "logs": logs})


@login_required
def harvest_form(request, plant_id):
    plant = get_object_or_404(Plant.objects.select_related("cutting__mother_plant__strain"), pk=plant_id)

    if request.method == "POST":
        try:
            HarvestService.document_harvest(
                plant=plant,
                harvest_date=date.fromisoformat(request.POST.get("harvest_date")),
                wet_weight=Decimal(request.POST.get("wet_weight", "0")),
                dry_weight=Decimal(request.POST.get("dry_weight", "0")),
                batch_code=request.POST.get("batch_code") or None,
            )
            messages.success(request, "Ernte dokumentiert")
            return redirect("cultivation:plant_detail", plant_id=plant.id)
        except (ValidationError, Exception) as exc:
            messages.error(request, str(exc))

    estimated_harvest = HarvestService.estimate_harvest_date(plant=plant)
    return render(
        request,
        "cultivation/harvest_form.html",
        {
            "plant": plant,
            "estimated_harvest": estimated_harvest,
        },
    )
