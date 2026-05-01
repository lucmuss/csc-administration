from django.urls import path

from .views import (
    add_to_cart,
    admin_confirm,
    admin_order_action,
    admin_order_list,
    cart,
    checkout,
    clear_cart,
    first_dispense_info,
    order_cancel_legacy,
    order_history,
    order_cancel,
    order_detail,
    order_list,
    remove_from_cart,
    shop,
)

app_name = "orders"

urlpatterns = [
    path("shop/", shop, name="shop"),
    path("cart/", cart, name="cart"),
    path("cart/add/", add_to_cart, name="add_to_cart"),
    path("cart/remove/", remove_from_cart, name="remove_from_cart"),
    path("cart/clear/", clear_cart, name="clear_cart"),
    path("checkout/", checkout, name="checkout"),
    path("first-dispense-info/", first_dispense_info, name="first_dispense_info"),
    path("my/", order_list, name="list"),
    path("my/<int:order_id>/", order_detail, name="detail"),
    path("history/", order_history, name="history"),
    path("my/<int:order_id>/cancel/", order_cancel, name="cancel"),
    path("cancel/<int:pk>/", order_cancel_legacy, name="cancel_legacy"),
    path("admin/", admin_order_list, name="admin_list"),
    path("admin/confirm/<int:pk>/", admin_confirm, name="admin_confirm"),
    path("admin/<int:order_id>/action/", admin_order_action, name="admin_action"),
]
