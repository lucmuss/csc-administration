# cultivation/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from django.conf import settings
from io import BytesIO
import uuid

# Optional: QR-Code Support
try:
    import qrcode
    import qrcode.image.svg
    QR_CODE_AVAILABLE = True
except ImportError:
    QR_CODE_AVAILABLE = False

from .models import GrowCycle, Plant, PlantLog, HarvestBatch
from .forms import (
    GrowCycleForm, PlantForm, PlantLogForm, HarvestBatchForm,
    HarvestBatchUpdateForm, PlantStatusUpdateForm
)
from apps.inventory.models import InventoryItem, InventoryLocation, Strain
from apps.members.models import Profile


# ==================== DASHBOARD ====================

@login_required
@permission_required("cultivation.view_growcycle", raise_exception=True)
def cultivation_dashboard(request):
    """Cultivation Dashboard mit Übersicht"""
    from datetime import date, timedelta
    
    # Aktive Grow Cycles
    active_cycles = GrowCycle.objects.filter(
        status__in=[GrowCycle.STATUS_PLANNED, GrowCycle.STATUS_ACTIVE]
    ).order_by("expected_harvest_date")
    
    # Pflanzen-Statistiken
    plant_stats = Plant.objects.aggregate(
        total=Count("id"),
        growing=Count("id", filter=Q(status__in=[
            Plant.STATUS_GROWING, Plant.STATUS_VEGETATIVE, Plant.STATUS_FLOWERING
        ])),
        harvested=Count("id", filter=Q(status=Plant.STATUS_HARVESTED)),
        drying=Count("id", filter=Q(status=Plant.STATUS_DRYING)),
        curing=Count("id", filter=Q(status=Plant.STATUS_CURING)),
    )
    
    # Ertrags-Statistiken
    yield_stats = HarvestBatch.objects.filter(
        assigned_to_inventory=True
    ).aggregate(
        total_dried=Sum("total_weight_dried"),
        total_batches=Count("id")
    )
    
    # Anstehende Ernten (nächste 30 Tage)
    upcoming_harvests = GrowCycle.objects.filter(
        status=GrowCycle.STATUS_ACTIVE,
        expected_harvest_date__lte=date.today() + timedelta(days=30)
    ).order_by("expected_harvest_date")[:5]
    
    # Aktive Batches in Trocknung/Aushärtung
    active_batches = HarvestBatch.objects.filter(
        assigned_to_inventory=False,
        curing_end_date__isnull=True
    ).order_by("-harvest_date")[:5]
    
    context = {
        "active_cycles": active_cycles,
        "plant_stats": plant_stats,
        "yield_stats": yield_stats,
        "upcoming_harvests": upcoming_harvests,
        "active_batches": active_batches,
    }
    return render(request, "cultivation/dashboard.html", context)


# ==================== GROW CYCLES ====================

@login_required
@permission_required("cultivation.view_growcycle", raise_exception=True)
def grow_cycle_list(request):
    """Liste aller Grow Cycles"""
    cycles = GrowCycle.objects.select_related("responsible_member").all()
    
    # Filter
    status_filter = request.GET.get("status")
    if status_filter:
        cycles = cycles.filter(status=status_filter)
    
    return render(request, "cultivation/grow_cycle_list.html", {
        "cycles": cycles,
        "status_choices": GrowCycle.STATUS_CHOICES
    })


@login_required
@permission_required("cultivation.add_growcycle", raise_exception=True)
def grow_cycle_create(request):
    """Neuen Grow Cycle erstellen"""
    if request.method == "POST":
        form = GrowCycleForm(request.POST)
        if form.is_valid():
            cycle = form.save(commit=False)
            cycle.created_by = request.user
            cycle.save()
            messages.success(request, f"Grow Cycle '{cycle.name}' wurde erstellt.")
            return redirect("cultivation:grow_cycle_detail", pk=cycle.pk)
    else:
        form = GrowCycleForm()
    
    return render(request, "cultivation/grow_cycle_form.html", {
        "form": form,
        "title": "Neuer Grow Cycle"
    })


@login_required
@permission_required("cultivation.view_growcycle", raise_exception=True)
def grow_cycle_detail(request, pk):
    """Detailansicht eines Grow Cycles"""
    cycle = get_object_or_404(
        GrowCycle.objects.prefetch_related("plants__strain"),
        pk=pk
    )
    
    plants = cycle.plants.all()
    
    context = {
        "cycle": cycle,
        "plants": plants,
        "plant_stats": {
            "total": plants.count(),
            "active": plants.filter(status__in=[
                Plant.STATUS_GROWING, Plant.STATUS_VEGETATIVE, Plant.STATUS_FLOWERING
            ]).count(),
            "harvested": plants.filter(status=Plant.STATUS_HARVESTED).count(),
        }
    }
    return render(request, "cultivation/grow_cycle_detail.html", context)


@login_required
@permission_required("cultivation.change_growcycle", raise_exception=True)
def grow_cycle_edit(request, pk):
    """Grow Cycle bearbeiten"""
    cycle = get_object_or_404(GrowCycle, pk=pk)
    
    if request.method == "POST":
        form = GrowCycleForm(request.POST, instance=cycle)
        if form.is_valid():
            form.save()
            messages.success(request, f"Grow Cycle '{cycle.name}' wurde aktualisiert.")
            return redirect("cultivation:grow_cycle_detail", pk=cycle.pk)
    else:
        form = GrowCycleForm(instance=cycle)
    
    return render(request, "cultivation/grow_cycle_form.html", {
        "form": form,
        "cycle": cycle,
        "title": "Grow Cycle bearbeiten"
    })


@login_required
@permission_required("cultivation.delete_growcycle", raise_exception=True)
def grow_cycle_delete(request, pk):
    """Grow Cycle löschen"""
    cycle = get_object_or_404(GrowCycle, pk=pk)
    
    if request.method == "POST":
        name = cycle.name
        cycle.delete()
        messages.success(request, f"Grow Cycle '{name}' wurde gelöscht.")
        return redirect("cultivation:grow_cycle_list")
    
    return render(request, "cultivation/grow_cycle_confirm_delete.html", {"cycle": cycle})


@login_required
@permission_required("cultivation.change_growcycle", raise_exception=True)
def grow_cycle_update_status(request, pk):
    """Status eines Grow Cycles aktualisieren"""
    cycle = get_object_or_404(GrowCycle, pk=pk)
    
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in [s[0] for s in GrowCycle.STATUS_CHOICES]:
            cycle.status = new_status
            
            if new_status == GrowCycle.STATUS_HARVESTED:
                from datetime import date
                cycle.actual_harvest_date = date.today()
            elif new_status == GrowCycle.STATUS_COMPLETED:
                from datetime import date
                cycle.completion_date = date.today()
            
            cycle.save()
            messages.success(request, f"Status wurde auf '{cycle.get_status_display()}' aktualisiert.")
        
    return redirect("cultivation:grow_cycle_detail", pk=cycle.pk)


# ==================== PLANTS ====================

@login_required
@permission_required("cultivation.view_plant", raise_exception=True)
def plant_list(request):
    """Liste aller Pflanzen"""
    plants = Plant.objects.select_related("strain", "grow_cycle").all()
    
    # Filter
    status_filter = request.GET.get("status")
    strain_filter = request.GET.get("strain")
    cycle_filter = request.GET.get("cycle")
    
    if status_filter:
        plants = plants.filter(status=status_filter)
    if strain_filter:
        plants = plants.filter(strain_id=strain_filter)
    if cycle_filter:
        plants = plants.filter(grow_cycle_id=cycle_filter)
    
    paginator = Paginator(plants, 25)
    page = request.GET.get("page")
    plants_page = paginator.get_page(page)
    
    context = {
        "plants": plants_page,
        "status_choices": Plant.STATUS_CHOICES,
        "strains": Strain.objects.all(),
        "cycles": GrowCycle.objects.all(),
    }
    return render(request, "cultivation/plant_list.html", context)


@login_required
@permission_required("cultivation.add_plant", raise_exception=True)
def plant_create(request):
    """Neue Pflanze erstellen"""
    # Optional: Vorausgewählter Grow Cycle
    cycle_id = request.GET.get("cycle")
    initial = {}
    if cycle_id:
        initial["grow_cycle"] = cycle_id
    
    if request.method == "POST":
        form = PlantForm(request.POST)
        if form.is_valid():
            plant = form.save(commit=False)
            plant.created_by = request.user
            plant.save()
            messages.success(request, f"Pflanze '{plant}' wurde erstellt.")
            return redirect("cultivation:plant_detail", pk=plant.pk)
    else:
        form = PlantForm(initial=initial)
    
    return render(request, "cultivation/plant_form.html", {
        "form": form,
        "title": "Neue Pflanze"
    })


@login_required
@permission_required("cultivation.view_plant", raise_exception=True)
def plant_detail(request, pk):
    """Detailansicht einer Pflanze"""
    plant = get_object_or_404(
        Plant.objects.select_related("strain", "grow_cycle", "grow_cycle__responsible_member"),
        pk=pk
    )
    
    # Logs
    logs = plant.logs.select_related("performed_by").all()[:20]
    
    # QR-Code
    qr_url = request.build_absolute_uri(f"/cultivation/plants/{plant.pk}/")
    
    context = {
        "plant": plant,
        "logs": logs,
        "qr_url": qr_url,
    }
    return render(request, "cultivation/plant_detail.html", context)


@login_required
@permission_required("cultivation.change_plant", raise_exception=True)
def plant_edit(request, pk):
    """Pflanze bearbeiten"""
    plant = get_object_or_404(Plant, pk=pk)
    
    if request.method == "POST":
        form = PlantForm(request.POST, instance=plant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Pflanze '{plant}' wurde aktualisiert.")
            return redirect("cultivation:plant_detail", pk=plant.pk)
    else:
        form = PlantForm(instance=plant)
    
    return render(request, "cultivation/plant_form.html", {
        "form": form,
        "plant": plant,
        "title": "Pflanze bearbeiten"
    })


@login_required
@permission_required("cultivation.delete_plant", raise_exception=True)
def plant_delete(request, pk):
    """Pflanze löschen"""
    plant = get_object_or_404(Plant, pk=pk)
    
    if request.method == "POST":
        name = str(plant)
        plant.delete()
        messages.success(request, f"Pflanze '{name}' wurde gelöscht.")
        return redirect("cultivation:plant_list")
    
    return render(request, "cultivation/plant_confirm_delete.html", {"plant": plant})


@login_required
@permission_required("cultivation.change_plant", raise_exception=True)
def plant_update_status(request, pk):
    """Status einer Pflanze aktualisieren"""
    plant = get_object_or_404(Plant, pk=pk)
    
    if request.method == "POST":
        form = PlantStatusUpdateForm(request.POST, instance=plant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Status wurde auf '{plant.get_status_display()}' aktualisiert.")
        else:
            messages.error(request, "Fehler beim Aktualisieren des Status.")
    
    return redirect("cultivation:plant_detail", pk=plant.pk)


@login_required
def plant_qr_code(request, pk):
    """QR-Code für eine Pflanze generieren"""
    plant = get_object_or_404(Plant, pk=pk)
    
    if not QR_CODE_AVAILABLE:
        # Fallback: Einfacher Text mit URL
        url = request.build_absolute_uri(f"/cultivation/plants/{plant.pk}/")
        response = HttpResponse(f"QR-Code: {url}", content_type="text/plain")
        return response
    
    # URL für die Pflanze
    url = request.build_absolute_uri(f"/cultivation/plants/{plant.pk}/")
    
    # QR-Code generieren
    factory = qrcode.image.svg.SvgImage
    qr = qrcode.make(url, image_factory=factory)
    
    # Als SVG ausgeben
    buffer = BytesIO()
    qr.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type="image/svg+xml")
    response["Content-Disposition"] = f'inline; filename="plant_{plant.qr_code_id}.svg"'
    return response


# ==================== PLANT LOGS ====================

@login_required
@permission_required("cultivation.add_plantlog", raise_exception=True)
def plant_log_create(request, plant_pk):
    """Neuen Log-Eintrag für eine Pflanze erstellen"""
    plant = get_object_or_404(Plant, pk=plant_pk)
    
    if request.method == "POST":
        form = PlantLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.plant = plant
            log.created_by = request.user
            log.save()
            messages.success(request, "Log-Eintrag wurde erstellt.")
            return redirect("cultivation:plant_detail", pk=plant.pk)
    else:
        form = PlantLogForm(initial={"date": timezone.now()})
    
    return render(request, "cultivation/plant_log_form.html", {
        "form": form,
        "plant": plant,
        "title": "Neuer Log-Eintrag"
    })


@login_required
@permission_required("cultivation.view_plantlog", raise_exception=True)
def plant_log_list(request, plant_pk):
    """Alle Logs einer Pflanze anzeigen"""
    plant = get_object_or_404(Plant, pk=plant_pk)
    logs = plant.logs.select_related("performed_by").all()
    
    paginator = Paginator(logs, 20)
    page = request.GET.get("page")
    logs_page = paginator.get_page(page)
    
    return render(request, "cultivation/plant_log_list.html", {
        "plant": plant,
        "logs": logs_page
    })


# ==================== HARVEST BATCHES ====================

@login_required
@permission_required("cultivation.view_harvestbatch", raise_exception=True)
def harvest_list(request):
    """Liste aller Ernte-Batches"""
    batches = HarvestBatch.objects.prefetch_related("plants__strain").all()
    
    # Filter
    status_filter = request.GET.get("status")
    if status_filter == "inventory":
        batches = batches.filter(assigned_to_inventory=True)
    elif status_filter == "processing":
        batches = batches.filter(assigned_to_inventory=False)
    
    return render(request, "cultivation/harvest_list.html", {
        "batches": batches,
    })


@login_required
@permission_required("cultivation.add_harvestbatch", raise_exception=True)
def harvest_create(request):
    """Neuen Ernte-Batch erstellen"""
    if request.method == "POST":
        form = HarvestBatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.created_by = request.user
            batch.save()
            form.save_m2m()  # Speichere Many-to-Many Beziehungen
            
            # Aktualisiere Pflanzen-Status
            for plant in batch.plants.all():
                plant.status = Plant.STATUS_HARVESTED
                plant.harvest_date = batch.harvest_date
                plant.save()
            
            messages.success(request, f"Ernte-Batch '{batch.batch_number}' wurde erstellt.")
            return redirect("cultivation:harvest_detail", pk=batch.pk)
    else:
        form = HarvestBatchForm()
    
    return render(request, "cultivation/harvest_form.html", {
        "form": form,
        "title": "Neue Ernte"
    })


@login_required
@permission_required("cultivation.view_harvestbatch", raise_exception=True)
def harvest_detail(request, pk):
    """Detailansicht eines Ernte-Batches"""
    batch = get_object_or_404(
        HarvestBatch.objects.prefetch_related("plants__strain", "plants__grow_cycle"),
        pk=pk
    )
    
    context = {
        "batch": batch,
        "can_assign_to_inventory": batch.is_ready_for_inventory,
    }
    return render(request, "cultivation/harvest_detail.html", context)


@login_required
@permission_required("cultivation.change_harvestbatch", raise_exception=True)
def harvest_edit(request, pk):
    """Ernte-Batch bearbeiten"""
    batch = get_object_or_404(HarvestBatch, pk=pk)
    
    if request.method == "POST":
        form = HarvestBatchUpdateForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ernte-Batch '{batch.batch_number}' wurde aktualisiert.")
            return redirect("cultivation:harvest_detail", pk=batch.pk)
    else:
        form = HarvestBatchUpdateForm(instance=batch)
    
    return render(request, "cultivation/harvest_update_form.html", {
        "form": form,
        "batch": batch,
        "title": "Ernte aktualisieren"
    })


@login_required
@permission_required("cultivation.delete_harvestbatch", raise_exception=True)
def harvest_delete(request, pk):
    """Ernte-Batch löschen"""
    batch = get_object_or_404(HarvestBatch, pk=pk)
    
    if request.method == "POST":
        batch_number = batch.batch_number
        batch.delete()
        messages.success(request, f"Ernte-Batch '{batch_number}' wurde gelöscht.")
        return redirect("cultivation:harvest_list")
    
    return render(request, "cultivation/harvest_confirm_delete.html", {"batch": batch})


@login_required
@permission_required("cultivation.change_harvestbatch", raise_exception=True)
def harvest_assign_to_inventory(request, pk):
    """Ernte-Batch dem Inventar zuweisen"""
    batch = get_object_or_404(HarvestBatch, pk=pk)
    
    if not batch.is_ready_for_inventory:
        messages.error(request, "Dieser Batch ist noch nicht bereit für die Inventar-Zuweisung.")
        return redirect("cultivation:harvest_detail", pk=batch.pk)
    
    if request.method == "POST":
        location_id = request.POST.get("location")
        
        try:
            with transaction.atomic():
                location = InventoryLocation.objects.get(pk=location_id)
                
                # Erstelle oder aktualisiere Inventory Item
                # Annahme: Ein Batch hat einen Haupt-Strain (oder wir erstellen pro Strain)
                strain = batch.plants.first().strain
                
                inventory_item, created = InventoryItem.objects.get_or_create(
                    strain=strain,
                    location=location,
                    defaults={"quantity": 0}
                )
                
                # Füge Menge hinzu
                inventory_item.quantity += batch.total_weight_dried
                inventory_item.save()
                
                # Markiere Batch als zugewiesen
                batch.assigned_to_inventory = True
                batch.inventory_item = inventory_item
                batch.save()
                
                messages.success(request, f"Batch wurde dem Inventar zugewiesen: {inventory_item}")
                
        except InventoryLocation.DoesNotExist:
            messages.error(request, "Standort nicht gefunden.")
        except Exception as e:
            messages.error(request, f"Fehler: {str(e)}")
        
        return redirect("cultivation:harvest_detail", pk=batch.pk)
    
    # Verfügbare Standorte
    locations = InventoryLocation.objects.all()
    
    return render(request, "cultivation/harvest_assign_inventory.html", {
        "batch": batch,
        "locations": locations
    })


# ==================== API ENDPOINTS ====================

@login_required
def api_plant_stats(request):
    """API: Pflanzen-Statistiken als JSON"""
    stats = Plant.objects.aggregate(
        total=Count("id"),
        growing=Count("id", filter=Q(status=Plant.STATUS_GROWING)),
        vegetative=Count("id", filter=Q(status=Plant.STATUS_VEGETATIVE)),
        flowering=Count("id", filter=Q(status=Plant.STATUS_FLOWERING)),
        harvested=Count("id", filter=Q(status=Plant.STATUS_HARVESTED)),
        drying=Count("id", filter=Q(status=Plant.STATUS_DRYING)),
        curing=Count("id", filter=Q(status=Plant.STATUS_CURING)),
    )
    
    return JsonResponse(stats)


@login_required
def api_grow_cycle_stats(request, pk):
    """API: Statistiken für einen Grow Cycle"""
    cycle = get_object_or_404(GrowCycle, pk=pk)
    
    stats = {
        "plant_count": cycle.plant_count,
        "days_active": cycle.days_active,
        "days_until_harvest": cycle.days_until_harvest,
        "expected_yield": float(cycle.total_expected_yield),
        "actual_yield": float(cycle.total_actual_yield),
    }
    
    return JsonResponse(stats)
