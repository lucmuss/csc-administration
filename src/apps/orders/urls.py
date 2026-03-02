from django.urls import path

from .views import add_to_cart, cart, checkout, clear_cart, order_list, shop

app_name = "orders"

urlpatterns = [
    path("shop/", shop, name="shop"),
    path("cart/", cart, name="cart"),
    path("cart/add/", add_to_cart, name="add_to_cart"),
    path("cart/clear/", clear_cart, name="clear_cart"),
    path("checkout/", checkout, name="checkout"),
    path("my/", order_list, name="list"),
]
