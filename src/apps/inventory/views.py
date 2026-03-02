from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Strain


@login_required
def strain_list(request):
    strains = Strain.objects.filter(is_active=True).order_by("name")
    return render(request, "inventory/strain_list.html", {"strains": strains})
