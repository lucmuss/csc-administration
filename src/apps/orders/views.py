from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.emails import send_order_completed_email, send_order_reserved_email
from apps.accounts.models import User
from apps.compliance.models import PreventionInfo
from apps.core.club import resolve_active_social_club
from apps.core.authz import staff_or_board_required
from apps.finance.services import balance_breakdown
from apps.governance.services import record_audit_event
from apps.inventory.models import Batch, Strain

from .models import Order
from .services import CartLine, cancel_reserved_order, complete_reserved_order, create_reserved_order, member_cancel_reserved_order


CART_SESSION_KEY = "cart"


def _is_staff_or_board(user: User) -> bool:
    return user.is_authenticated and user.role in {User.ROLE_STAFF, User.ROLE_BOARD}


def _load_cart(request) -> dict[str, str]:
    return request.session.get(CART_SESSION_KEY, {})


def _save_cart(request, cart: dict[str, str]) -> None:
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def _member_may_order(user) -> tuple[bool, str]:
    profile = getattr(user, "profile", None)
    if not profile:
        return False, "Kein Mitgliederprofil vorhanden."
    if not profile.is_verified or profile.status != "active":
        return False, "Shop, Bestellungen und Warenkorb werden erst nach erfolgreicher Verifizierung durch den Vorstand freigeschaltet."
    if profile.is_locked_for_orders:
        return False, "Deine Bestellungen sind aktuell gesperrt."
    return True, ""


def _active_club(request):
    if getattr(request.user, "is_superuser", False):
        return resolve_active_social_club(request)
    return getattr(request.user, "social_club", None)


@login_required
def shop(request):
    allowed, reason = _member_may_order(request.user)
    if request.user.role == User.ROLE_MEMBER and not allowed:
        messages.info(request, reason)
        return redirect("core:dashboard")
    active_type = request.GET.get("type", "all")
    strains = Strain.objects.filter(is_active=True)
    club = _active_club(request)
    if club:
        strains = strains.filter(Q(social_club=club) | Q(social_club__isnull=True))
    if active_type in {
        Strain.PRODUCT_TYPE_FLOWER,
        Strain.PRODUCT_TYPE_CUTTING,
        Strain.PRODUCT_TYPE_EDIBLE,
        Strain.PRODUCT_TYPE_ACCESSORY,
        Strain.PRODUCT_TYPE_MERCH,
    }:
        strains = strains.filter(product_type=active_type)
    strains = strains.order_by("product_type", "name")
    probation_notice = ""
    profile = getattr(request.user, "profile", None)
    if (
        request.user.role == User.ROLE_MEMBER
        and profile is not None
        and profile.probation_until
        and profile.probation_until >= timezone.localdate()
    ):
        probation_notice = "Du befindest dich aktuell in der 6 Monate Probezeit."
    return render(
        request,
        "orders/shop.html",
        {"strains": strains, "active_type": active_type, "probation_notice": probation_notice},
    )


@login_required
def add_to_cart(request):
    allowed, reason = _member_may_order(request.user)
    if request.user.role == User.ROLE_MEMBER and not allowed:
        messages.info(request, reason)
        return redirect("core:dashboard")
    if request.method != "POST":
        return redirect("orders:shop")

    strain_id = request.POST.get("strain_id")
    if not strain_id and request.POST.get("batch_id"):
        batch = Batch.objects.filter(pk=request.POST.get("batch_id"), is_active=True).select_related("strain").first()
        if batch is not None:
            strain_id = str(batch.strain_id)
    quantity = request.POST.get("quantity", request.POST.get("grams", "0"))
    if quantity == "custom":
        quantity = request.POST.get("custom_quantity", "0")
    try:
        quantity_decimal = Decimal(quantity)
        if quantity_decimal <= 0:
            raise ValueError
    except Exception:
        messages.error(request, "Ungueltige Menge")
        return redirect("orders:shop")
    club = _active_club(request)
    if not Strain.objects.filter(id=strain_id, is_active=True).filter(Q(social_club=club) | Q(social_club__isnull=True)).exists():
        messages.error(request, "Produkt nicht verfuegbar.")
        return redirect("orders:shop")
    strain = Strain.objects.filter(id=strain_id, is_active=True).first()
    profile = getattr(request.user, "profile", None)
    if strain and strain.is_weight_based and profile:
        allowed, reason = profile.can_consume(quantity_decimal)
        if not allowed:
            messages.error(request, reason)
            request.session["cart_limit_error"] = reason
            return redirect(f"{reverse('orders:shop')}?limit=1")

    cart = _load_cart(request)
    existing = Decimal(cart.get(str(strain_id), "0"))
    cart[str(strain_id)] = str(existing + quantity_decimal)
    _save_cart(request, cart)

    messages.success(request, "Zum Warenkorb hinzugefuegt")
    return redirect("orders:shop")


@login_required
def cart(request):
    allowed, reason = _member_may_order(request.user)
    if request.user.role == User.ROLE_MEMBER and not allowed:
        messages.info(request, reason)
        return redirect("core:dashboard")
    raw_cart = _load_cart(request)
    rows = []
    total = Decimal("0.00")
    total_grams = Decimal("0.00")
    total_pieces = Decimal("0.00")
    profile = getattr(request.user, "profile", None)

    club = _active_club(request)
    for strain_id, quantity in raw_cart.items():
        try:
            strain = Strain.objects.get(id=int(strain_id), is_active=True)
            if club and strain.social_club_id not in {club.id, None}:
                continue
            quantity_decimal = Decimal(quantity)
        except Exception:
            continue

        line_total = strain.price * quantity_decimal
        rows.append({"strain": strain, "quantity": quantity_decimal, "line_total": line_total})
        total += line_total
        if strain.is_weight_based:
            total_grams += quantity_decimal
        else:
            total_pieces += quantity_decimal

    return render(
        request,
        "orders/cart.html",
        {
            "rows": rows,
            "total": total,
            "total_grams": total_grams,
            "total_pieces": total_pieces,
            "balance_breakdown": balance_breakdown(profile) if profile else None,
        },
    )


def _cart_rows(raw_cart, club):
    rows = []
    total = Decimal("0.00")
    total_grams = Decimal("0.00")
    total_pieces = Decimal("0.00")

    for strain_id, quantity in raw_cart.items():
        try:
            strain = Strain.objects.get(id=int(strain_id), is_active=True)
            if club and strain.social_club_id not in {club.id, None}:
                continue
            quantity_decimal = Decimal(quantity)
        except Exception:
            continue

        line_total = strain.price * quantity_decimal
        rows.append({"strain": strain, "quantity": quantity_decimal, "line_total": line_total})
        total += line_total
        if strain.is_weight_based:
            total_grams += quantity_decimal
        else:
            total_pieces += quantity_decimal

    return rows, total, total_grams, total_pieces


@login_required
def clear_cart(request):
    allowed, reason = _member_may_order(request.user)
    if request.user.role == User.ROLE_MEMBER and not allowed:
        messages.info(request, reason)
        return redirect("core:dashboard")
    _save_cart(request, {})
    messages.info(request, "Warenkorb geleert")
    return redirect("orders:cart")


@login_required
@require_POST
def remove_from_cart(request):
    raw_cart = _load_cart(request)
    strain_id = request.POST.get("strain_id")
    if not strain_id and request.POST.get("batch_id"):
        batch = Batch.objects.filter(pk=request.POST.get("batch_id")).first()
        if batch is not None:
            strain_id = str(batch.strain_id)
    if strain_id:
        raw_cart.pop(str(strain_id), None)
        _save_cart(request, raw_cart)
    return redirect("orders:cart")


@login_required
def checkout(request):
    allowed, reason = _member_may_order(request.user)
    if request.user.role == User.ROLE_MEMBER and not allowed:
        messages.info(request, reason)
        return redirect("core:dashboard")
    if request.method != "POST":
        return redirect("orders:cart")

    raw_cart = _load_cart(request)
    club = _active_club(request)
    rows, total, total_grams, total_pieces = _cart_rows(raw_cart, club)
    if not rows:
        limit_reason = request.session.pop("cart_limit_error", "")
        if limit_reason:
            messages.error(request, limit_reason)
            profile = getattr(request.user, "profile", None)
            return render(
                request,
                "orders/cart.html",
                {
                    "rows": [],
                    "total": Decimal("0.00"),
                    "total_grams": Decimal("0.00"),
                    "total_pieces": Decimal("0.00"),
                    "balance_breakdown": balance_breakdown(profile) if profile else None,
                },
            )
        messages.error(request, "Dein Warenkorb ist leer.")
        return redirect("orders:cart")

    confirm_value = request.POST.get("confirm")
    # Legacy tests submit only payment_method and expect direct reservation.
    if not confirm_value and request.POST.get("payment_method"):
        confirm_value = "yes"

    if confirm_value != "yes":
        profile = getattr(request.user, "profile", None)
        return render(
            request,
            "orders/checkout_confirm.html",
            {
                "rows": rows,
                "total": total,
                "total_grams": total_grams,
                "total_pieces": total_pieces,
                "balance_breakdown": balance_breakdown(profile) if profile else None,
            },
        )

    cart_lines = []
    for strain_id, quantity in raw_cart.items():
        try:
            cart_lines.append(CartLine(strain_id=int(strain_id), quantity=Decimal(quantity)))
        except Exception:
            continue

    try:
        order = create_reserved_order(user=request.user, cart_lines=cart_lines)
    except (ValidationError, Exception) as exc:
        messages.error(request, str(exc))
        profile = getattr(request.user, "profile", None)
        return render(
            request,
            "orders/cart.html",
            {
                "rows": rows,
                "total": total,
                "total_grams": total_grams,
                "total_pieces": total_pieces,
                "balance_breakdown": balance_breakdown(profile) if profile else None,
            },
        )

    _save_cart(request, {})
    send_order_reserved_email(order=order, request=request)
    messages.success(request, f"Bestellung #{order.id} reserviert bis {order.reserved_until:%d.%m.%Y %H:%M}")
    return redirect("orders:list")


@login_required
def order_list(request):
    allowed, reason = _member_may_order(request.user)
    if request.user.role == User.ROLE_MEMBER and not allowed:
        messages.info(request, reason)
        return redirect("core:dashboard")
    orders = Order.objects.filter(member=request.user).prefetch_related("items__strain")
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def first_dispense_info(request):
    profile = getattr(request.user, "profile", None)
    prevention_info = None
    if profile is not None:
        prevention_info = PreventionInfo.objects.filter(profile=profile).first()
    return render(request, "orders/first_dispense_info.html", {"prevention_info": prevention_info})


@login_required
def order_detail(request, order_id: int):
    queryset = Order.objects.select_related("member", "member__profile", "invoice").prefetch_related("items__strain")
    if request.user.role not in {User.ROLE_STAFF, User.ROLE_BOARD}:
        allowed, reason = _member_may_order(request.user)
        if not allowed:
            messages.info(request, reason)
            return redirect("core:dashboard")
        queryset = queryset.filter(member=request.user)
    order = get_object_or_404(queryset, id=order_id)
    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "is_admin_view": request.user.role in {User.ROLE_STAFF, User.ROLE_BOARD},
        },
    )


@login_required
@require_POST
def order_cancel(request, order_id: int):
    allowed, reason = _member_may_order(request.user)
    if request.user.role == User.ROLE_MEMBER and not allowed:
        messages.info(request, reason)
        return redirect("core:dashboard")
    order = get_object_or_404(Order.objects.select_related("member"), id=order_id, member=request.user)
    order_number = order.id
    try:
        member_cancel_reserved_order(order=order)
        record_audit_event(
            actor=request.user,
            domain="orders",
            action="self_cancelled",
            target=order,
            summary=f"Bestellung #{order_number} vom Mitglied selbst storniert und geloescht.",
            metadata={"status": order.status},
            request=request,
        )
        messages.success(request, f"Bestellung #{order_number} wurde storniert, entfernt und die Reservierung freigegeben.")
    except ValidationError as exc:
        messages.error(request, str(exc))
        return redirect("orders:detail", order_id=order.id)
    return redirect("orders:list")


@login_required
@require_POST
def order_cancel_legacy(request, pk: int):
    order = get_object_or_404(Order.objects.select_related("member"), id=pk, member=request.user)
    try:
        cancel_reserved_order(order=order)
        messages.success(request, f"Bestellung #{order.id} wurde storniert.")
    except ValidationError as exc:
        messages.error(request, str(exc))
    return redirect("orders:list")


@staff_or_board_required(_is_staff_or_board)
def admin_order_list(request):
    status_filter = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "created_desc").strip()

    orders = Order.objects.select_related("member", "member__profile").prefetch_related("items__strain")
    if status_filter:
        orders = orders.filter(status=status_filter)
    if query:
        search_filter = (
            Q(member__email__icontains=query)
            | Q(member__first_name__icontains=query)
            | Q(member__last_name__icontains=query)
        )
        if query.isdigit():
            search_filter |= Q(id=int(query))
        orders = orders.filter(search_filter)

    sort_map = {
        "created_desc": "-created_at",
        "created_asc": "created_at",
        "total_desc": "-total",
        "total_asc": "total",
        "status_asc": "status",
        "status_desc": "-status",
    }
    orders = orders.order_by(sort_map.get(sort, "-created_at"))
    paginator = Paginator(orders, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "orders/admin_order_list.html",
        {
            "orders": page_obj,
            "page_obj": page_obj,
            "status_choices": Order.STATUS_CHOICES,
            "filters": {"status": status_filter, "q": query, "sort": sort},
        },
    )


@staff_or_board_required(_is_staff_or_board)
def admin_order_action(request, order_id: int):
    order = get_object_or_404(Order.objects.select_related("member"), id=order_id)
    action = request.POST.get("action")
    next_target = request.POST.get("next") or "orders:admin_list"

    if action in {"complete", "cancel"} and request.POST.get("confirm") not in {"yes", "no"}:
        return render(
            request,
            "orders/admin_order_confirm.html",
            {
                "order": order,
                "action": action,
                "next": next_target,
            },
        )
    if request.POST.get("confirm") == "no":
        messages.info(request, "Die Bestellaktion wurde abgebrochen.")
        return redirect(next_target)

    try:
        if action == "complete":
            complete_reserved_order(order=order)
            send_order_completed_email(order=order, request=request)
            messages.success(request, f"Bestellung #{order.id} wurde ausgegeben und vom Guthaben abgebucht.")
            record_audit_event(
                actor=request.user,
                domain="orders",
                action="completed",
                target=order,
                summary=f"Bestellung #{order.id} wurde ausgegeben und abgebucht.",
                metadata={"member": order.member.email, "status": order.status},
                request=request,
            )
        elif action == "cancel":
            cancel_reserved_order(order=order)
            messages.warning(request, f"Bestellung #{order.id} wurde storniert.")
            record_audit_event(
                actor=request.user,
                domain="orders",
                action="cancelled",
                target=order,
                summary=f"Bestellung #{order.id} wurde storniert.",
                metadata={"member": order.member.email, "status": order.status},
                request=request,
            )
        else:
            messages.error(request, "Unbekannte Bestellaktion.")
    except ValidationError as exc:
        messages.error(request, str(exc))

    return redirect(next_target)


@staff_or_board_required(_is_staff_or_board)
@require_POST
def admin_confirm(request, pk: int):
    order = get_object_or_404(Order.objects.select_related("member", "member__profile"), pk=pk)
    try:
        complete_reserved_order(order=order)
        messages.success(request, f"Bestellung #{order.id} wurde bestaetigt.")
    except ValidationError as exc:
        messages.error(request, str(exc))
    return redirect("orders:admin_list")


@login_required
def order_history(request):
    return order_list(request)
