import csv
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.models import User
from apps.orders.models import OrderItem

from .forms import BalanceTopUpForm, SepaMandateForm, UploadedInvoiceForm, UploadedInvoiceUpdateForm
from .models import BalanceTopUp, BalanceTransaction, Invoice, Payment, UploadedInvoice
from .services import (
    active_sepa_mandate,
    analyze_uploaded_invoice,
    apply_monthly_membership_credits,
    balance_breakdown,
    create_sepa_mandate,
    create_stripe_checkout_for_topup,
    finalize_stripe_topup,
    invoice_archive_summary,
    render_invoice_pdf,
)


def _statistics_items_queryset(selected_year: str):
    items = (
        OrderItem.objects.select_related("strain", "order")
        .filter(order__status="completed")
        .order_by("order__updated_at", "id")
    )
    if selected_year.isdigit():
        items = items.filter(order__updated_at__year=int(selected_year))
    return items


def _build_statistics_payload(items):
    monthly = {}
    product_totals = defaultdict(lambda: {"quantity": 0, "revenue": 0, "product_type": "", "unit": ""})
    flower_products = defaultdict(lambda: {"quantity": 0, "revenue": 0})
    cutting_products = defaultdict(lambda: {"quantity": 0, "revenue": 0})

    for item in items:
        month_start = item.order.updated_at.date().replace(day=1)
        row = monthly.setdefault(
            month_start,
            {
                "label": month_start.strftime("%m.%Y"),
                "flower_grams": 0,
                "cuttings": 0,
                "edibles": 0,
                "accessories": 0,
                "merch": 0,
                "revenue": 0,
            },
        )
        quantity = float(item.quantity_grams)
        revenue = float(item.total_price)
        row["revenue"] += revenue
        if item.strain.product_type == item.strain.PRODUCT_TYPE_FLOWER:
            row["flower_grams"] += quantity
            flower_products[item.strain.name]["quantity"] += quantity
            flower_products[item.strain.name]["revenue"] += revenue
        elif item.strain.product_type == item.strain.PRODUCT_TYPE_CUTTING:
            row["cuttings"] += quantity
            cutting_products[item.strain.name]["quantity"] += quantity
            cutting_products[item.strain.name]["revenue"] += revenue
        elif item.strain.product_type == item.strain.PRODUCT_TYPE_EDIBLE:
            row["edibles"] += quantity
        elif item.strain.product_type == item.strain.PRODUCT_TYPE_ACCESSORY:
            row["accessories"] += quantity
        elif item.strain.product_type == item.strain.PRODUCT_TYPE_MERCH:
            row["merch"] += quantity

        product_entry = product_totals[item.strain.name]
        product_entry["quantity"] += quantity
        product_entry["revenue"] += revenue
        product_entry["product_type"] = item.strain.get_product_type_display()
        product_entry["unit"] = item.strain.unit_label

    month_rows = []
    flower_max = max((row["flower_grams"] for row in monthly.values()), default=0) or 1
    unit_max = max(
        (
            max(row["cuttings"], row["edibles"], row["accessories"], row["merch"])
            for row in monthly.values()
        ),
        default=0,
    ) or 1
    for month_start, row in sorted(monthly.items(), reverse=True):
        row["month_start"] = month_start
        row["flower_width"] = max((row["flower_grams"] / flower_max) * 100, 6) if row["flower_grams"] else 0
        row["cuttings_width"] = max((row["cuttings"] / unit_max) * 100, 6) if row["cuttings"] else 0
        row["edibles_width"] = max((row["edibles"] / unit_max) * 100, 6) if row["edibles"] else 0
        row["accessories_width"] = max((row["accessories"] / unit_max) * 100, 6) if row["accessories"] else 0
        row["merch_width"] = max((row["merch"] / unit_max) * 100, 6) if row["merch"] else 0
        month_rows.append(row)

    product_rows = []
    product_max = max((entry["quantity"] for entry in product_totals.values()), default=0) or 1
    for name, entry in sorted(product_totals.items(), key=lambda item: item[1]["quantity"], reverse=True)[:12]:
        product_rows.append(
            {
                "name": name,
                "product_type": entry["product_type"],
                "quantity": entry["quantity"],
                "revenue": entry["revenue"],
                "unit": entry["unit"],
                "width": max((entry["quantity"] / product_max) * 100, 8),
            }
        )

    def _typed_rows(source, unit):
        typed_max = max((entry["quantity"] for entry in source.values()), default=0) or 1
        rows = []
        for name, entry in sorted(source.items(), key=lambda item: item[1]["quantity"], reverse=True)[:8]:
            rows.append(
                {
                    "name": name,
                    "quantity": entry["quantity"],
                    "revenue": entry["revenue"],
                    "unit": unit,
                    "width": max((entry["quantity"] / typed_max) * 100, 8),
                }
            )
        return rows

    summary = {
        "months": len(month_rows),
        "flower_grams_total": round(sum(row["flower_grams"] for row in month_rows), 2),
        "units_total": round(
            sum(row["cuttings"] + row["edibles"] + row["accessories"] + row["merch"] for row in month_rows), 2
        ),
        "revenue_total": round(sum(row["revenue"] for row in month_rows), 2),
        "cuttings_total": round(sum(row["cuttings"] for row in month_rows), 2),
    }

    return {
        "month_rows": month_rows,
        "product_rows": product_rows,
        "flower_rows": _typed_rows(flower_products, "g"),
        "cutting_rows": _typed_rows(cutting_products, "Stk."),
        "summary": summary,
    }


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


@login_required
def archive(request):
    if request.user.role not in {User.ROLE_STAFF, User.ROLE_BOARD}:
        raise Http404

    if request.method == "POST":
        form = UploadedInvoiceForm(request.POST, request.FILES, current_user=request.user)
        if form.is_valid():
            uploaded_invoice = form.save(commit=False)
            uploaded_invoice.created_by = request.user
            if not uploaded_invoice.title:
                uploaded_invoice.title = uploaded_invoice.document.name.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip()
            uploaded_invoice.save()
            analyze_uploaded_invoice(uploaded_invoice)
            if uploaded_invoice.extraction_status == UploadedInvoice.EXTRACTION_SUCCESS:
                messages.success(request, "Rechnung gespeichert und per KI analysiert.")
            else:
                messages.warning(
                    request,
                    "Rechnung gespeichert. Die KI-Auswertung konnte nicht vollstaendig abgeschlossen werden.",
                )
            return redirect("finance:archive_detail", pk=uploaded_invoice.pk)
    else:
        form = UploadedInvoiceForm(current_user=request.user)

    invoices = UploadedInvoice.objects.select_related("assigned_to", "created_by").all()
    direction = request.GET.get("direction", "").strip()
    payment_status = request.GET.get("payment_status", "").strip()
    year = request.GET.get("year", "").strip()
    month = request.GET.get("month", "").strip()
    if direction:
        invoices = invoices.filter(direction=direction)
    if payment_status:
        invoices = invoices.filter(payment_status=payment_status)
    if year.isdigit():
        invoices = invoices.filter(issue_date__year=int(year))
    if month.isdigit():
        invoices = invoices.filter(issue_date__month=int(month))

    years = UploadedInvoice.objects.exclude(issue_date__isnull=True).dates("issue_date", "year", order="DESC")
    return render(
        request,
        "finance/archive.html",
        {
            "form": form,
            "invoices": invoices,
            "years": years,
            "filters": {
                "direction": direction,
                "payment_status": payment_status,
                "year": year,
                "month": month,
            },
            "summary": invoice_archive_summary(invoices),
        },
    )


@login_required
def statistics(request):
    if request.user.role not in {User.ROLE_STAFF, User.ROLE_BOARD}:
        raise Http404

    selected_year = request.GET.get("year", "").strip()
    items = _statistics_items_queryset(selected_year)
    payload = _build_statistics_payload(items)
    all_years = (
        OrderItem.objects.filter(order__status="completed")
        .dates("order__updated_at", "year", order="DESC")
    )
    available_years = [entry.year for entry in all_years]
    comparison = None
    comparison_year = None
    effective_year = int(selected_year) if selected_year.isdigit() else (available_years[0] if available_years else None)
    if effective_year:
        comparison_year = effective_year - 1
        previous_payload = _build_statistics_payload(_statistics_items_queryset(str(comparison_year)))

        def _delta(current_value, previous_value):
            if not previous_value:
                return None
            return round(((current_value - previous_value) / previous_value) * 100, 1)

        comparison = {
            "reference_year": comparison_year,
            "flower_delta": _delta(payload["summary"]["flower_grams_total"], previous_payload["summary"]["flower_grams_total"]),
            "revenue_delta": _delta(payload["summary"]["revenue_total"], previous_payload["summary"]["revenue_total"]),
            "cuttings_delta": _delta(payload["summary"]["cuttings_total"], previous_payload["summary"]["cuttings_total"]),
            "previous_summary": previous_payload["summary"],
        }

    if request.GET.get("format") == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        year_suffix = selected_year or "alle-jahre"
        response["Content-Disposition"] = f'attachment; filename="csc-statistiken-{year_suffix}.csv"'
        writer = csv.writer(response, delimiter=";")
        writer.writerow(["Zeitraum", selected_year or "Alle Jahre"])
        writer.writerow(["Monate im Filter", payload["summary"]["months"]])
        writer.writerow(["Blueten gesamt (g)", payload["summary"]["flower_grams_total"]])
        writer.writerow(["Stecklinge gesamt (Stk.)", payload["summary"]["cuttings_total"]])
        writer.writerow(["Stueckartikel gesamt", payload["summary"]["units_total"]])
        writer.writerow(["Umsatz gesamt (EUR)", payload["summary"]["revenue_total"]])
        writer.writerow([])
        writer.writerow(["Monat", "Blueten (g)", "Stecklinge", "Edibles", "Rauchzubehoer", "Werbegeschenke", "Umsatz (EUR)"])
        for row in payload["month_rows"]:
            writer.writerow(
                [
                    row["label"],
                    row["flower_grams"],
                    row["cuttings"],
                    row["edibles"],
                    row["accessories"],
                    row["merch"],
                    row["revenue"],
                ]
            )
        writer.writerow([])
        writer.writerow(["Top-Produkte", "Typ", "Menge", "Einheit", "Umsatz (EUR)"])
        for row in payload["product_rows"]:
            writer.writerow([row["name"], row["product_type"], row["quantity"], row["unit"], row["revenue"]])
        return response

    return render(
        request,
        "finance/statistics.html",
        {
            **payload,
            "available_years": available_years,
            "selected_year": selected_year,
            "comparison": comparison,
            "effective_year": effective_year,
        },
    )


@login_required
def archive_detail(request, pk: int):
    if request.user.role not in {User.ROLE_STAFF, User.ROLE_BOARD}:
        raise Http404
    uploaded_invoice = get_object_or_404(UploadedInvoice.objects.select_related("assigned_to", "created_by"), pk=pk)
    if request.method == "POST":
        if request.POST.get("action") == "reanalyze":
            analyze_uploaded_invoice(uploaded_invoice)
            if uploaded_invoice.extraction_status == UploadedInvoice.EXTRACTION_SUCCESS:
                messages.success(request, "Rechnung erneut analysiert.")
            else:
                messages.warning(request, "Die erneute Analyse konnte nicht vollstaendig abgeschlossen werden.")
            return redirect("finance:archive_detail", pk=uploaded_invoice.pk)
        form = UploadedInvoiceUpdateForm(request.POST, instance=uploaded_invoice)
        if form.is_valid():
            form.save()
            messages.success(request, "Rechnung aktualisiert.")
            return redirect("finance:archive_detail", pk=uploaded_invoice.pk)
    else:
        form = UploadedInvoiceUpdateForm(instance=uploaded_invoice)
    return render(
        request,
        "finance/archive_detail.html",
        {
            "uploaded_invoice": uploaded_invoice,
            "form": form,
        },
    )
