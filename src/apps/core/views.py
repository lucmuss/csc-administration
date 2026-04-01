from decimal import Decimal

from django.conf import settings as django_settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from django.db.models import Count, Q, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.core.authz import staff_or_board_required
from apps.compliance.models import ComplianceReport, SuspiciousActivity
from apps.cultivation.models import GrowCycle, HarvestBatch, Plant
from apps.finance.models import Invoice, Payment
from apps.governance.services import send_due_meeting_notifications
from apps.inventory.models import InventoryCount, InventoryItem, Strain
from apps.members.models import Profile
from apps.orders.models import Order
from apps.participation.models import MemberEngagement, Shift, WorkHours

from .forms import PublicDocumentForm
from .models import PublicDocument

LOW_STOCK_THRESHOLD = Decimal(django_settings.LOW_STOCK_THRESHOLD_EUR)
MEMBER_CAPACITY = django_settings.MEMBER_CAPACITY


def _is_staff_or_board(user: User) -> bool:
    return bool(getattr(user, "is_authenticated", False) and getattr(user, "role", "") in {User.ROLE_STAFF, User.ROLE_BOARD})


def _is_board(user: User) -> bool:
    return bool(getattr(user, "is_authenticated", False) and getattr(user, "role", "") == User.ROLE_BOARD)


def _request_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return (request.META.get("REMOTE_ADDR") or "").strip()


def _configured_service_providers() -> list[str]:
    providers = list(django_settings.CLUB_EXTERNAL_SERVICES)
    if django_settings.STRIPE_SECRET_KEY and "Stripe" not in providers:
        providers.append("Stripe fuer Online-Zahlungen und Guthabenaufladungen")
    if django_settings.OPENROUTER_API_KEY and "OpenRouter" not in providers:
        providers.append("OpenRouter fuer optionale KI-gestuetzte Rechnungserkennung")
    if django_settings.GA_TRACKING_ID and "Google Analytics" not in providers:
        providers.append("Google Analytics nach ausdruecklicher Einwilligung")
    return providers


def _legal_setup_complete() -> bool:
    required = [
        django_settings.CLUB_NAME,
        django_settings.CLUB_CONTACT_ADDRESS,
        django_settings.CLUB_CONTACT_EMAIL,
        django_settings.CLUB_BOARD_REPRESENTATIVES,
        django_settings.CLUB_REGISTER_COURT,
        django_settings.CLUB_TAX_NUMBER,
    ]
    return all(bool(value) for value in required)


def _module_links():
    return [
        {
            "title": "Mitglieder-Cockpit",
            "description": "Offene Bewerbungen, Mitgliedsstatus und CSV-Export.",
            "href": "/members/admin/",
            "tone": "forest",
        },
        {
            "title": "Bestellungen",
            "description": "Reservierungen pruefen, freigeben oder stornieren.",
            "href": "/orders/admin/",
            "tone": "ink",
        },
        {
            "title": "Finanzstatus",
            "description": "Rechnungen, SEPA und offene Forderungen.",
            "href": "/finance/",
            "tone": "sand",
        },
        {
            "title": "Compliance",
            "description": "Verdachtsfaelle, Jahresmeldung und Risikohinweise.",
            "href": "/compliance/",
            "tone": "ember",
        },
        {
            "title": "Messaging",
            "description": "Newsletter, SMS und Vorlagenverwaltung.",
            "href": "/messaging/",
            "tone": "ink",
        },
        {
            "title": "Mein Profil",
            "description": "Eigene Stammdaten, SEPA und persoenliche Angaben pflegen.",
            "href": "/members/profile/",
            "tone": "forest",
        },
    ]


def _table_set():
    return set(connection.introspection.table_names())


def _cultivation_tables_ready():
    tables = _table_set()
    required = {
        GrowCycle._meta.db_table,
        Plant._meta.db_table,
        HarvestBatch._meta.db_table,
    }
    return required.issubset(tables)


@login_required
def dashboard(request):
    send_due_meeting_notifications()
    today = timezone.localdate()
    now = timezone.now()
    profile = Profile.objects.filter(user=request.user).first()
    recent_orders = (
        Order.objects.filter(member=request.user)
        .prefetch_related("items__strain")
        .order_by("-created_at")[:5]
    )

    context = {
        "profile": profile,
        "recent_orders": recent_orders,
    }

    if request.user.role in {User.ROLE_STAFF, User.ROLE_BOARD}:
        total_members = Profile.objects.count()
        active_members = Profile.objects.filter(status=Profile.STATUS_ACTIVE).count()
        pending_members = (
            Profile.objects.select_related("user")
            .filter(status=Profile.STATUS_PENDING)
            .order_by("created_at")[:8]
        )
        low_stock_strains = (
            Strain.objects.filter(is_active=True, stock__lte=LOW_STOCK_THRESHOLD)
            .order_by("stock", "name")[:8]
        )
        open_invoices_qs = (
            Invoice.objects.select_related("profile__user")
            .filter(status=Invoice.STATUS_OPEN)
            .order_by("due_date")
        )
        suspicious_qs = (
            SuspiciousActivity.objects.select_related("profile__user")
            .filter(is_reported=False)
            .order_by("-detected_at")
        )
        upcoming_shifts = Shift.objects.filter(starts_at__gte=now).order_by("starts_at")[:6]
        latest_report = ComplianceReport.objects.order_by("-year").first()
        latest_count = InventoryCount.objects.order_by("-date", "-id").first()
        total_stock = Strain.objects.filter(is_active=True).aggregate(total=Sum("stock"))["total"] or Decimal("0.00")
        reserved_orders = Order.objects.filter(status=Order.STATUS_RESERVED).count()
        overdue_invoices = open_invoices_qs.filter(due_date__lt=today).count()
        work_hours_open = WorkHours.objects.filter(approved=False).count()
        engagement_open = MemberEngagement.objects.filter(registration_completed=False).count()
        if _cultivation_tables_ready():
            cultivation_overview = {
                "cycle_count": GrowCycle.objects.filter(
                    status__in=[GrowCycle.STATUS_PLANNED, GrowCycle.STATUS_ACTIVE]
                ).count(),
                "plant_count": Plant.objects.exclude(status__in=[Plant.STATUS_COMPLETED, Plant.STATUS_DEAD]).count(),
                "harvest_count": HarvestBatch.objects.count(),
            }
        else:
            cultivation_overview = {
                "cycle_count": 0,
                "plant_count": 0,
                "harvest_count": 0,
            }

        context.update(
            {
                "board_mode": True,
                "dashboard_date": today,
                "capacity_ratio": min(total_members / MEMBER_CAPACITY, 1) if MEMBER_CAPACITY else 0,
                "capacity_percent": round((total_members / MEMBER_CAPACITY) * 100, 1) if MEMBER_CAPACITY else 0,
                "member_capacity_remaining": max(MEMBER_CAPACITY - total_members, 0),
                "summary_cards": [
                    {
                        "label": "Aktive Mitglieder",
                        "value": active_members,
                        "detail": f"{total_members}/{MEMBER_CAPACITY} belegt",
                        "tone": "forest",
                        "href": "/members/admin/",
                    },
                    {
                        "label": "Reservierte Ausgaben",
                        "value": reserved_orders,
                        "detail": "offene Warenkoerbe mit Reservierung",
                        "tone": "sand",
                        "href": "/orders/admin/?status=reserved",
                    },
                    {
                        "label": "Offene Forderungen",
                        "value": open_invoices_qs.count(),
                        "detail": f"{overdue_invoices} ueberfaellig",
                        "tone": "ember",
                        "href": "/finance/invoices/",
                    },
                    {
                        "label": "Offene Compliance-Faelle",
                        "value": suspicious_qs.count(),
                        "detail": "ungeklaerte Hinweise",
                        "tone": "ink",
                        "href": "/compliance/suspicious-activities/",
                    },
                ],
                "pending_members": pending_members,
                "low_stock_strains": low_stock_strains,
                "open_invoices": open_invoices_qs[:8],
                "suspicious_open": suspicious_qs[:8],
                "upcoming_shifts": upcoming_shifts,
                "latest_report": latest_report,
                "latest_count": latest_count,
                "total_stock": total_stock,
                "work_hours_open": work_hours_open,
                "engagement_open": engagement_open,
                "cultivation_overview": cultivation_overview,
                "module_links": _module_links(),
            }
        )
    else:
        context["board_mode"] = False
        context["pending_member_limited_access"] = bool(
            profile
            and profile.status == Profile.STATUS_PENDING
            and profile.onboarding_complete
        )

    return render(request, "core/dashboard.html", context)


def privacy(request):
    return render(
        request,
        "core/privacy.html",
        {
            "club_service_providers": _configured_service_providers(),
            "legal_setup_complete": _legal_setup_complete(),
            "club_legal_basis_notice": django_settings.CLUB_LEGAL_BASIS_NOTICE,
            "club_retention_notice": django_settings.CLUB_RETENTION_NOTICE,
        },
    )


def imprint(request):
    return render(
        request,
        "core/imprint.html",
        {
            "club_name": django_settings.CLUB_NAME,
            "club_contact_address": django_settings.CLUB_CONTACT_ADDRESS,
            "club_contact_email": django_settings.CLUB_CONTACT_EMAIL,
            "club_contact_phone": django_settings.CLUB_CONTACT_PHONE,
            "club_board_representatives": django_settings.CLUB_BOARD_REPRESENTATIVES,
            "club_register_entry": django_settings.CLUB_REGISTER_ENTRY,
            "club_vat_id": django_settings.CLUB_VAT_ID,
            "club_supervisory_authority": django_settings.CLUB_SUPERVISORY_AUTHORITY,
            "club_content_responsible": django_settings.CLUB_CONTENT_RESPONSIBLE,
            "club_membership_email": django_settings.CLUB_MEMBERSHIP_EMAIL,
            "club_prevention_email": django_settings.CLUB_PREVENTION_EMAIL,
            "club_finance_email": django_settings.CLUB_FINANCE_EMAIL,
            "club_privacy_contact": django_settings.CLUB_PRIVACY_CONTACT,
            "club_data_protection_officer": django_settings.CLUB_DATA_PROTECTION_OFFICER,
            "club_language_notice": django_settings.CLUB_LANGUAGE_NOTICE,
            "club_register_court": django_settings.CLUB_REGISTER_COURT,
            "club_tax_number": django_settings.CLUB_TAX_NUMBER,
            "club_responsible_person": django_settings.CLUB_RESPONSIBLE_PERSON,
            "legal_setup_complete": _legal_setup_complete(),
        },
    )


def documents(request):
    documents_qs = PublicDocument.objects.filter(is_public=True)
    return render(request, "core/documents.html", {"documents": documents_qs})


@staff_or_board_required(_is_staff_or_board)
def documents_admin(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delete":
            document = get_object_or_404(PublicDocument, pk=request.POST.get("document_id"))
            title = document.title
            document.delete()
            messages.warning(request, f"Dokument {title} wurde geloescht.")
            return redirect("core:documents_admin")
        form = PublicDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Dokument wurde gespeichert.")
            return redirect("core:documents_admin")
    else:
        form = PublicDocumentForm()
    return render(
        request,
        "core/documents_admin.html",
        {
            "form": form,
            "documents": PublicDocument.objects.order_by("display_order", "title"),
        },
    )

def health(request):
    request_ip = _request_ip(request)
    if request_ip not in django_settings.HEALTH_ALLOWED_IPS and not _is_staff_or_board(getattr(request, "user", None)):
        return HttpResponseForbidden("Health endpoint is restricted.")
    return JsonResponse({"status": "ok", "service": "csc-administration"})


def ready(request):
    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        db_ok = False

    return JsonResponse(
        {
            "status": "ready" if db_ok else "degraded",
            "database": "ok" if db_ok else "error",
        },
        status=200 if db_ok else 503,
    )
