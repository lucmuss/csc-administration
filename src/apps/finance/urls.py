from django.urls import path

from .views import (
    add_balance,
    archive,
    archive_detail,
    balance,
    dashboard,
    invoice_detail,
    invoice_list,
    invoice_pay,
    invoice_pdf,
    mandate_create,
    payment_list,
    sepa_mandate_create,
    sepa_mandate_revoke,
    statistics,
    stripe_method_create,
    stripe_method_success,
    topup_create,
    topup_success,
)

app_name = "finance"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("balance/", balance, name="balance"),
    path("members/<int:member_id>/add-balance/", add_balance, name="add_balance"),
    path("archive/", archive, name="archive"),
    path("archive/<int:pk>/", archive_detail, name="archive_detail"),
    path("statistics/", statistics, name="statistics"),
    path("mandate/new/", mandate_create, name="mandate_create"),
    path("sepa/mandate/create/", sepa_mandate_create, name="sepa_mandate_create"),
    path("sepa/mandate/<int:pk>/revoke/", sepa_mandate_revoke, name="sepa_mandate_revoke"),
    path("stripe-method/new/", stripe_method_create, name="stripe_method_create"),
    path("stripe-method/success/", stripe_method_success, name="stripe_method_success"),
    path("payments/", payment_list, name="payment_list"),
    path("invoices/", invoice_list, name="invoice_list"),
    path("invoices/<int:pk>/", invoice_detail, name="invoice_detail"),
    path("invoices/<int:pk>/pay/", invoice_pay, name="invoice_pay"),
    path("invoices/<int:pk>/pdf/", invoice_pdf, name="invoice_pdf"),
    path("topup/", topup_create, name="topup_create"),
    path("topup/success/", topup_success, name="topup_success"),
]
