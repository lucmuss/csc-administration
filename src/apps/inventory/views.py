from datetime import date

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from .models import InventoryCount, InventoryItem, InventoryLocation, Strain
from .services import InventoryCountService


@login_required
def strain_list(request):
    active_type = request.GET.get("type", "all")
    strains = Strain.objects.filter(is_active=True)
    if active_type in {
        Strain.PRODUCT_TYPE_FLOWER,
        Strain.PRODUCT_TYPE_CUTTING,
        Strain.PRODUCT_TYPE_EDIBLE,
    }:
        strains = strains.filter(product_type=active_type)
    strains = strains.order_by("product_type", "name")
    return render(request, "inventory/strain_list.html", {"strains": strains, "active_type": active_type})


@login_required
def location_list(request):
    locations = InventoryLocation.objects.prefetch_related("items__strain").all()
    return render(request, "inventory/location_list.html", {"locations": locations})


@login_required
def inventory_count_form(request):
    items = InventoryItem.objects.select_related("strain", "location").all()

    if request.method == "POST":
        counted_quantities = {}
        for item in items:
            raw = request.POST.get(f"item_{item.id}")
            if raw in (None, ""):
                continue
            counted_quantities[item.id] = raw

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
