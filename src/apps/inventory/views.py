from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import formset_factory
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404

from apps.core.club import resolve_active_social_club
from apps.core.authz import staff_or_board_required

from .forms import InventoryCountValueField, InventoryLocationForm, StrainForm
from .models import Batch, InventoryCount, InventoryItem, InventoryLocation, Strain
from .services import InventoryCountService


def _is_staff_or_board(user) -> bool:
    return user.is_authenticated and getattr(user, "role", "") in {"staff", "board"}


def _active_club(request):
    if getattr(request.user, "is_superuser", False):
        return resolve_active_social_club(request)
    return getattr(request.user, "social_club", None)


@login_required
def strain_list(request):
    active_type = request.GET.get("type", "all")
    thc_min = request.GET.get("thc_min", "").strip()
    strains = Strain.objects.filter(is_active=True)
    club = _active_club(request)
    if club:
        strains = strains.filter(Q(social_club=club) | Q(social_club__isnull=True))
    if active_type in {
        Strain.PRODUCT_TYPE_FLOWER,
        Strain.PRODUCT_TYPE_CUTTING,
        Strain.PRODUCT_TYPE_EDIBLE,
        Strain.PRODUCT_TYPE_ACCESSORY,
        Strain.PRODUCT_TYPE_MERCH,
    }:
        strains = strains.filter(product_type=active_type)
    if thc_min:
        try:
            strains = strains.filter(thc__gte=Decimal(thc_min))
        except Exception:
            pass
    strains = strains.order_by("product_type", "name")
    return render(
        request,
        "inventory/strain_list.html",
        {
            "strains": strains,
            "active_type": active_type,
            "can_manage_inventory": _is_staff_or_board(request.user),
        },
    )


@login_required
def location_list(request):
    locations = InventoryLocation.objects.prefetch_related("items__strain").all()
    return render(
        request,
        "inventory/location_list.html",
        {
            "locations": locations,
            "can_manage_inventory": _is_staff_or_board(request.user),
        },
    )


@staff_or_board_required(_is_staff_or_board)
def location_create(request):
    if request.method == "POST":
        form = InventoryLocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f"Lagerort {location.name} wurde angelegt.")
            return redirect("inventory:location_edit", pk=location.pk)
    else:
        form = InventoryLocationForm()
    return render(
        request,
        "inventory/location_form.html",
        {"form": form, "title": "Neuen Lagerort anlegen", "location": None},
    )


@staff_or_board_required(_is_staff_or_board)
def location_edit(request, pk: int):
    location = get_object_or_404(InventoryLocation, pk=pk)
    if request.method == "POST":
        form = InventoryLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f"Lagerort {location.name} wurde aktualisiert.")
            return redirect("inventory:location_edit", pk=location.pk)
    else:
        form = InventoryLocationForm(instance=location)
    return render(
        request,
        "inventory/location_form.html",
        {"form": form, "title": f"Lagerort bearbeiten: {location.name}", "location": location},
    )


@staff_or_board_required(_is_staff_or_board)
def location_delete(request, pk: int):
    location = get_object_or_404(InventoryLocation, pk=pk)
    if request.method == "POST":
        location_name = location.name
        location.delete()
        messages.warning(request, f"Lagerort {location_name} wurde geloescht.")
    return redirect("inventory:location_list")


@staff_or_board_required(_is_staff_or_board)
def strain_create(request):
    if request.method == "POST":
        data = request.POST.copy()
        if "thc_content" in data and "thc" not in data:
            data["thc"] = data["thc_content"]
        if "cbd_content" in data and "cbd" not in data:
            data["cbd"] = data["cbd_content"]
        if "price_per_gram" in data and "price" not in data:
            data["price"] = data["price_per_gram"]
        data.setdefault("product_type", Strain.PRODUCT_TYPE_FLOWER)
        data.setdefault("card_tone", Strain.CARD_TONE_APRICOT)
        data.setdefault("quality_grade", Strain.QUALITY_B)
        data.setdefault("stock", "1000.00")
        data.setdefault("is_active", "on")
        form = StrainForm(data, request.FILES)
        if form.is_valid():
            strain = form.save(commit=False)
            strain.social_club = _active_club(request)
            strain.save()
            messages.success(request, f"Produkt {strain.name} wurde angelegt.")
            return redirect("inventory:strain_edit", pk=strain.pk)
    else:
        form = StrainForm()
    return render(request, "inventory/strain_form.html", {"form": form, "title": "Neues Produkt anlegen", "strain": None})


@login_required
def strain_detail(request, pk: int):
    strain = get_object_or_404(Strain, pk=pk, is_active=True)
    club = _active_club(request)
    if club and strain.social_club_id != club.id:
        messages.error(request, "Dieses Produkt gehoert zu einem anderen Social Club.")
        return redirect("inventory:strain_list")
    return render(
        request,
        "inventory/strain_detail.html",
        {
            "strain": strain,
            "can_manage_inventory": _is_staff_or_board(request.user),
        },
    )


@staff_or_board_required(_is_staff_or_board)
def strain_edit(request, pk: int):
    strain = get_object_or_404(Strain, pk=pk)
    club = _active_club(request)
    if club and strain.social_club_id != club.id:
        messages.error(request, "Dieses Produkt gehoert zu einem anderen Social Club.")
        return redirect("inventory:strain_list")
    if request.method == "POST":
        data = request.POST.copy()
        if "thc_content" in data and "thc" not in data:
            data["thc"] = data["thc_content"]
        if "cbd_content" in data and "cbd" not in data:
            data["cbd"] = data["cbd_content"]
        if "price_per_gram" in data and "price" not in data:
            data["price"] = data["price_per_gram"]
        data.setdefault("product_type", strain.product_type)
        data.setdefault("card_tone", strain.card_tone)
        data.setdefault("quality_grade", strain.quality_grade)
        data.setdefault("stock", str(strain.stock))
        data.setdefault("is_active", "on" if strain.is_active else "")
        form = StrainForm(data, request.FILES, instance=strain)
        if form.is_valid():
            form.save()
            messages.success(request, f"Produkt {strain.name} wurde aktualisiert.")
            return redirect("inventory:strain_edit", pk=strain.pk)
    else:
        form = StrainForm(instance=strain)
    return render(request, "inventory/strain_form.html", {"form": form, "title": f"Produkt bearbeiten: {strain.name}", "strain": strain})


@login_required
def inventory_count_form(request):
    items = InventoryItem.objects.select_related("strain", "location").all()

    if request.method == "POST":
        counted_quantities = {}
        for item in items:
            raw = request.POST.get(f"item_{item.id}")
            if raw in (None, ""):
                continue
            field = InventoryCountValueField(min_value=Decimal("0"), required=False)
            try:
                counted_quantities[item.id] = field.clean(raw)
            except ValidationError as exc:
                messages.error(request, f"{item.strain.name}: {exc.messages[0]}")
                return render(request, "inventory/inventory_count_form.html", {"items": items})

        try:
            count = InventoryCountService.perform_count(
                count_date=date.today(),
                counted_quantities=counted_quantities,
            )
            messages.success(request, f"Inventur gespeichert ({count.items_counted} Positionen)")
            return redirect("inventory:discrepancy_report")
        except Exception as exc:
            messages.error(request, str(exc))

    return render(request, "inventory/inventory_count_form.html", {"items": items})


@login_required
def discrepancy_report(request):
    counts = InventoryCount.objects.all()[:20]
    return render(request, "inventory/discrepancy_report.html", {"counts": counts})


@staff_or_board_required(_is_staff_or_board)
def strain_delete(request, pk: int):
    strain = get_object_or_404(Strain, pk=pk)
    if request.method == "POST":
        if strain.batches.exists():
            messages.error(request, "Sorte kann nicht geloescht werden, solange Chargen vorhanden sind.")
            return redirect("inventory:strain_edit", pk=strain.pk)
        strain.delete()
        messages.success(request, "Sorte wurde geloescht.")
    return redirect("inventory:strain_list")


@staff_or_board_required(_is_staff_or_board)
def batch_create(request):
    context = {"title": "Neue Charge", "error": "", "batch": None}
    if request.method == "POST":
        try:
            strain = Strain.objects.get(pk=request.POST.get("strain"))
            batch_number = (request.POST.get("batch_number") or "").strip()
            harvest_date = request.POST.get("harvest_date") or None
            total_harvested = Decimal(request.POST.get("total_harvested_grams") or "0")
            available = Decimal(request.POST.get("available_grams") or "0")
            if available > total_harvested:
                context["error"] = "Verfuegbarer Bestand darf nicht groesser als Erntemenge sein."
            elif not batch_number:
                context["error"] = "Chargennummer fehlt."
            else:
                batch = Batch.objects.create(
                    strain=strain,
                    batch_number=batch_number,
                    harvest_date=harvest_date,
                    total_harvested_grams=total_harvested,
                    available_grams=available,
                    status=Batch.STATUS_AVAILABLE,
                )
                messages.success(request, "Charge wurde angelegt.")
                return redirect("inventory:batch_detail", pk=batch.pk)
        except (Strain.DoesNotExist, ValidationError, ValueError) as exc:
            context["error"] = str(exc)
    context["strains"] = Strain.objects.filter(is_active=True).order_by("name")
    return render(request, "inventory/batch_form.html", context)


@login_required
def batch_detail(request, pk: int):
    batch = get_object_or_404(Batch.objects.select_related("strain"), pk=pk)
    return render(request, "inventory/batch_detail.html", {"batch": batch})


@staff_or_board_required(_is_staff_or_board)
def batch_delete(request, pk: int):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == "POST":
        batch.delete()
        messages.success(request, "Charge wurde geloescht.")
    return redirect("inventory:dashboard")


@login_required
def dashboard(request):
    batches = Batch.objects.select_related("strain").order_by("quantity", "-created_at")
    low_stock_batches = [batch for batch in batches if batch.quantity <= Decimal("10.00")]
    return render(
        request,
        "inventory/dashboard.html",
        {"batches": batches, "low_stock_batches": low_stock_batches},
    )


@staff_or_board_required(_is_staff_or_board)
def strain_update(request, pk: int):
    return strain_edit(request, pk=pk)
