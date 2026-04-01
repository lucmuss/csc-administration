from django.urls import path

from .views import archive, archive_detail, dashboard, invoice_detail, invoice_list, invoice_pdf, mandate_create, payment_list, topup_create, topup_success

app_name = "finance"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("archive/", archive, name="archive"),
    path("archive/<int:pk>/", archive_detail, name="archive_detail"),
    path("mandate/new/", mandate_create, name="mandate_create"),
    path("payments/", payment_list, name="payment_list"),
    path("invoices/", invoice_list, name="invoice_list"),
    path("invoices/<int:pk>/", invoice_detail, name="invoice_detail"),
    path("invoices/<int:pk>/pdf/", invoice_pdf, name="invoice_pdf"),
    path("topup/", topup_create, name="topup_create"),
    path("topup/success/", topup_success, name="topup_success"),
]
