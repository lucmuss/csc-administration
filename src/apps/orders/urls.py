from django.urls import path

from .views import add_to_cart, admin_order_action, admin_order_list, cart, checkout, clear_cart, order_cancel, order_detail, order_list, shop

app_name = "orders"

urlpatterns = [
    path("shop/", shop, name="shop"),
    path("cart/", cart, name="cart"),
    path("cart/add/", add_to_cart, name="add_to_cart"),
    path("cart/clear/", clear_cart, name="clear_cart"),
    path("checkout/", checkout, name="checkout"),
    path("my/", order_list, name="list"),
    path("my/<int:order_id>/", order_detail, name="detail"),
    path("my/<int:order_id>/cancel/", order_cancel, name="cancel"),
    path("admin/", admin_order_list, name="admin_list"),
    path("admin/<int:order_id>/action/", admin_order_action, name="admin_action"),
]
