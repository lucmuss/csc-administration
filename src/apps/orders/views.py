from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from apps.inventory.models import Strain

from .models import Order
from .services import CartLine, create_reserved_order


CART_SESSION_KEY = "cart"


def _load_cart(request) -> dict[str, str]:
    return request.session.get(CART_SESSION_KEY, {})


def _save_cart(request, cart: dict[str, str]) -> None:
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


@login_required
def shop(request):
    strains = Strain.objects.filter(is_active=True).order_by("name")
    return render(request, "orders/shop.html", {"strains": strains})


@login_required
def add_to_cart(request):
    if request.method != "POST":
        return redirect("orders:shop")

    strain_id = request.POST.get("strain_id")
    grams = request.POST.get("grams", "0")
    try:
        grams_decimal = Decimal(grams)
        if grams_decimal <= 0:
            raise ValueError
    except Exception:
        messages.error(request, "Ungueltige Menge")
        return redirect("orders:shop")

    cart = _load_cart(request)
    existing = Decimal(cart.get(str(strain_id), "0"))
    cart[str(strain_id)] = str(existing + grams_decimal)
    _save_cart(request, cart)

    messages.success(request, "Zum Warenkorb hinzugefuegt")
    return redirect("orders:shop")


@login_required
def cart(request):
    raw_cart = _load_cart(request)
    rows = []
    total = Decimal("0.00")
    total_grams = Decimal("0.00")

    for strain_id, grams in raw_cart.items():
        try:
            strain = Strain.objects.get(id=int(strain_id), is_active=True)
            grams_decimal = Decimal(grams)
        except Exception:
            continue

        line_total = strain.price * grams_decimal
        rows.append({"strain": strain, "grams": grams_decimal, "line_total": line_total})
        total += line_total
        total_grams += grams_decimal

    return render(
        request,
        "orders/cart.html",
        {
            "rows": rows,
            "total": total,
            "total_grams": total_grams,
        },
    )


@login_required
def clear_cart(request):
    _save_cart(request, {})
    messages.info(request, "Warenkorb geleert")
    return redirect("orders:cart")


@login_required
def checkout(request):
    if request.method != "POST":
        return redirect("orders:cart")

    raw_cart = _load_cart(request)
    cart_lines = []
    for strain_id, grams in raw_cart.items():
        try:
            cart_lines.append(CartLine(strain_id=int(strain_id), grams=Decimal(grams)))
        except Exception:
            continue

    try:
        order = create_reserved_order(user=request.user, cart_lines=cart_lines)
    except (ValidationError, Exception) as exc:
        messages.error(request, str(exc))
        return redirect("orders:cart")

    _save_cart(request, {})
    messages.success(request, f"Bestellung #{order.id} reserviert bis {order.reserved_until:%d.%m.%Y %H:%M}")
    return redirect("orders:list")


@login_required
def order_list(request):
    orders = Order.objects.filter(member=request.user).prefetch_related("items__strain")
    return render(request, "orders/order_list.html", {"orders": orders})
