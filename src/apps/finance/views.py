from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.models import User

from .forms import BalanceTopUpForm, SepaMandateForm
from .models import BalanceTopUp, BalanceTransaction, Invoice, Payment
from .services import (
    active_sepa_mandate,
    apply_monthly_membership_credits,
    balance_breakdown,
    create_sepa_mandate,
    create_stripe_checkout_for_topup,
    finalize_stripe_topup,
    render_invoice_pdf,
)


@login_required
def dashboard(request):
    apply_monthly_membership_credits()
    profile = getattr(request.user, "profile", None)
    if profile:
        profile.refresh_from_db()
    open_invoices = Invoice.objects.none()
    pending_payments = Payment.objects.none()
    summary = None

    if request.user.role in {User.ROLE_STAFF, User.ROLE_BOARD}:
        open_invoices = (
            Invoice.objects.select_related("profile__user")
            .filter(status=Invoice.STATUS_OPEN)
            .order_by("due_date")[:12]
        )
        pending_payments = (
            Payment.objects.select_related("profile__user", "invoice", "mandate")
            .order_by("-created_at")[:12]
        )
        outstanding_total = (
            Invoice.objects.filter(status=Invoice.STATUS_OPEN).aggregate(total=Sum("amount"))["total"] or 0
        )
        summary = {
            "open_invoice_count": Invoice.objects.filter(status=Invoice.STATUS_OPEN).count(),
            "pending_sepa_count": Payment.objects.filter(status=Payment.STATUS_PENDING).count(),
            "returned_payment_count": Payment.objects.filter(status=Payment.STATUS_RETURNED).count(),
            "outstanding_total": outstanding_total,
        }
    elif profile:
        open_invoices = Invoice.objects.filter(profile=profile, status=Invoice.STATUS_OPEN).order_by("due_date")[:10]
        pending_payments = Payment.objects.filter(profile=profile).order_by("-created_at")[:10]
    breakdown = balance_breakdown(profile) if profile else None
    topup_form = BalanceTopUpForm() if profile and request.user.role == User.ROLE_MEMBER else None
    mandate = active_sepa_mandate(profile) if profile else None
    recent_balance_transactions = (
        profile.balance_transactions.all()[:10]
        if profile and hasattr(profile, "balance_transactions")
        else []
    )

    return render(
        request,
        "finance/dashboard.html",
        {
            "profile": profile,
            "open_invoices": open_invoices,
            "pending_payments": pending_payments,
            "summary": summary,
            "board_mode": request.user.role in {User.ROLE_STAFF, User.ROLE_BOARD},
            "balance_breakdown": breakdown,
            "topup_form": topup_form,
            "active_mandate": mandate,
            "recent_balance_transactions": recent_balance_transactions,
        },
    )


@login_required
def mandate_create(request):
    profile = getattr(request.user, "profile", None)
    existing_mandate = active_sepa_mandate(profile) if profile else None
    initial = {}
    if existing_mandate:
        initial = {
            "iban": existing_mandate.iban,
            "bic": existing_mandate.bic,
            "account_holder": existing_mandate.account_holder,
        }
    elif profile:
        initial = {
            "account_holder": profile.account_holder_name,
        }
    if request.method == "POST":
        form = SepaMandateForm(request.POST)
        if form.is_valid():
            if request.POST.get("confirm") == "yes":
                mandate = create_sepa_mandate(
                    user=request.user,
                    iban=form.cleaned_data["iban"],
                    bic=form.cleaned_data["bic"],
                    account_holder=form.cleaned_data["account_holder"],
                )
                messages.success(
                    request,
                    f"SEPA-Mandat {mandate.mandate_reference} {'aktualisiert' if existing_mandate else 'angelegt'}",
                )
                return redirect("finance:dashboard")
            if request.POST.get("confirm") == "no":
                messages.info(request, "Die Aenderung des SEPA-Mandats wurde abgebrochen.")
                return redirect("finance:mandate_create")
            return render(
                request,
                "finance/mandate_confirm.html",
                {
                    "form": form,
                    "existing_mandate": existing_mandate,
                    "changes_sensitive": bool(existing_mandate),
                },
            )
    else:
        form = SepaMandateForm(initial=initial)

    return render(
        request,
        "finance/mandate_form.html",
        {"form": form, "existing_mandate": existing_mandate},
    )


@login_required
def payment_list(request):
    profile = getattr(request.user, "profile", None)
    payments = Payment.objects.none()
    if request.user.role in {User.ROLE_STAFF, User.ROLE_BOARD}:
        payments = Payment.objects.select_related("invoice", "mandate", "profile__user").order_by("-created_at")
    elif profile:
        payments = Payment.objects.filter(profile=profile).select_related("invoice", "mandate").order_by("-created_at")
    return render(request, "finance/payment_list.html", {"payments": payments})


@login_required
def invoice_list(request):
    profile = getattr(request.user, "profile", None)
    invoices = Invoice.objects.none()
    if request.user.role in {User.ROLE_STAFF, User.ROLE_BOARD}:
        invoices = Invoice.objects.select_related("profile__user").order_by("-created_at")
    elif profile:
        invoices = Invoice.objects.filter(profile=profile).order_by("-created_at")
    return render(request, "finance/invoice_list.html", {"invoices": invoices})


def _invoice_queryset_for_user(user):
    if user.role in {User.ROLE_STAFF, User.ROLE_BOARD}:
        return Invoice.objects.select_related("profile__user", "order").prefetch_related("order__items__strain", "payments")
    if hasattr(user, "profile"):
        return Invoice.objects.filter(profile=user.profile).select_related("profile__user", "order").prefetch_related("order__items__strain", "payments")
    return Invoice.objects.none()


@login_required
def invoice_detail(request, pk: int):
    invoice = get_object_or_404(_invoice_queryset_for_user(request.user), pk=pk)
    return render(request, "finance/invoice_detail.html", {"invoice": invoice})


@login_required
def invoice_pdf(request, pk: int):
    invoice = get_object_or_404(_invoice_queryset_for_user(request.user), pk=pk)
    pdf = render_invoice_pdf(invoice)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{invoice.invoice_number}.pdf"'
    return response


@login_required
def topup_create(request):
    if request.user.role != User.ROLE_MEMBER:
        raise Http404
    form = BalanceTopUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        success_url = request.build_absolute_uri(reverse("finance:topup_success"))
        cancel_url = request.build_absolute_uri(reverse("finance:dashboard"))
        topup = create_stripe_checkout_for_topup(
            user=request.user,
            amount=form.cleaned_data["final_amount"],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        if topup.checkout_url:
            return redirect(topup.checkout_url)
        messages.error(request, topup.failure_reason or "Stripe-Aufladung ist aktuell nicht verfuegbar.")
        return redirect("finance:dashboard")
    if form.errors:
        messages.error(request, " ".join(error for errors in form.errors.values() for error in errors))
    else:
        messages.error(request, "Bitte gib einen gueltigen Betrag an.")
    return redirect("finance:dashboard")


@login_required
def topup_success(request):
    if request.user.role != User.ROLE_MEMBER:
        raise Http404
    topup_id = request.GET.get("topup_id")
    session_id = request.GET.get("session_id")
    topup = BalanceTopUp.objects.filter(id=topup_id, profile=request.user.profile).first()
    if not topup:
        messages.warning(request, "Die Aufladung konnte nicht gefunden werden.")
        return redirect("finance:dashboard")
    topup = finalize_stripe_topup(topup=topup, session_id=session_id)
    if topup.status == BalanceTopUp.STATUS_COMPLETED:
        messages.success(request, f"{topup.amount} EUR wurden deinem Guthaben gutgeschrieben.")
    else:
        messages.warning(request, "Die Stripe-Zahlung ist noch nicht bestaetigt. Bitte pruefe es gleich erneut.")
    return redirect("finance:dashboard")
