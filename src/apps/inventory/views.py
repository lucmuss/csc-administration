from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import formset_factory
from django.shortcuts import redirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test

from .forms import InventoryCountValueField, InventoryLocationForm, StrainForm
from .models import InventoryCount, InventoryItem, InventoryLocation, Strain
from .services import InventoryCountService


def _is_staff_or_board(user) -> bool:
    return user.is_authenticated and getattr(user, "role", "") in {"staff", "board"}


@login_required
def strain_list(request):
    active_type = request.GET.get("type", "all")
    strains = Strain.objects.filter(is_active=True)
    if active_type in {
        Strain.PRODUCT_TYPE_FLOWER,
        Strain.PRODUCT_TYPE_CUTTING,
        Strain.PRODUCT_TYPE_EDIBLE,
        Strain.PRODUCT_TYPE_ACCESSORY,
        Strain.PRODUCT_TYPE_MERCH,
    }:
        strains = strains.filter(product_type=active_type)
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


@user_passes_test(_is_staff_or_board)
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


@user_passes_test(_is_staff_or_board)
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


@user_passes_test(_is_staff_or_board)
def location_delete(request, pk: int):
    location = get_object_or_404(InventoryLocation, pk=pk)
    if request.method == "POST":
        location_name = location.name
        location.delete()
        messages.warning(request, f"Lagerort {location_name} wurde geloescht.")
    return redirect("inventory:location_list")


@user_passes_test(_is_staff_or_board)
def strain_create(request):
    if request.method == "POST":
        form = StrainForm(request.POST, request.FILES)
        if form.is_valid():
            strain = form.save()
            messages.success(request, f"Produkt {strain.name} wurde angelegt.")
            return redirect("inventory:strain_edit", pk=strain.pk)
    else:
        form = StrainForm()
    return render(request, "inventory/strain_form.html", {"form": form, "title": "Neues Produkt anlegen", "strain": None})


@login_required
def strain_detail(request, pk: int):
    strain = get_object_or_404(Strain, pk=pk, is_active=True)
    return render(
        request,
        "inventory/strain_detail.html",
        {
            "strain": strain,
            "can_manage_inventory": _is_staff_or_board(request.user),
        },
    )


@user_passes_test(_is_staff_or_board)
def strain_edit(request, pk: int):
    strain = get_object_or_404(Strain, pk=pk)
    if request.method == "POST":
        form = StrainForm(request.POST, request.FILES, instance=strain)
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
