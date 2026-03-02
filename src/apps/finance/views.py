from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import SepaMandateForm
from .models import Invoice, Payment
from .services import create_sepa_mandate


@login_required
def dashboard(request):
    profile = getattr(request.user, "profile", None)
    open_invoices = Invoice.objects.none()
    pending_payments = Payment.objects.none()
    if profile:
        open_invoices = Invoice.objects.filter(profile=profile, status=Invoice.STATUS_OPEN).order_by("due_date")[:10]
        pending_payments = Payment.objects.filter(profile=profile).order_by("-created_at")[:10]

    return render(
        request,
        "finance/dashboard.html",
        {
            "profile": profile,
            "open_invoices": open_invoices,
            "pending_payments": pending_payments,
        },
    )


@login_required
def mandate_create(request):
    if request.method == "POST":
        form = SepaMandateForm(request.POST)
        if form.is_valid():
            mandate = create_sepa_mandate(
                user=request.user,
                iban=form.cleaned_data["iban"],
                bic=form.cleaned_data["bic"],
                account_holder=form.cleaned_data["account_holder"],
            )
            messages.success(request, f"SEPA-Mandat {mandate.mandate_reference} angelegt")
            return redirect("finance:dashboard")
    else:
        form = SepaMandateForm()

    return render(request, "finance/mandate_form.html", {"form": form})


@login_required
def payment_list(request):
    profile = getattr(request.user, "profile", None)
    payments = Payment.objects.none()
    if profile:
        payments = Payment.objects.filter(profile=profile).select_related("invoice", "mandate").order_by("-created_at")
    return render(request, "finance/payment_list.html", {"payments": payments})


@login_required
def invoice_list(request):
    profile = getattr(request.user, "profile", None)
    invoices = Invoice.objects.none()
    if profile:
        invoices = Invoice.objects.filter(profile=profile).order_by("-created_at")
    return render(request, "finance/invoice_list.html", {"invoices": invoices})
