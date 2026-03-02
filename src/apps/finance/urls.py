from django.urls import path

from .views import dashboard, invoice_list, mandate_create, payment_list

app_name = "finance"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("mandate/new/", mandate_create, name="mandate_create"),
    path("payments/", payment_list, name="payment_list"),
    path("invoices/", invoice_list, name="invoice_list"),
]
