from decimal import Decimal

from django.conf import settings as django_settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from django.db.models import Count, Q, Sum
from django.forms import inlineformset_factory
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.core.club import (
    ACTIVE_FEDERAL_STATE_COOKIE,
    ACTIVE_FEDERAL_STATE_SESSION_KEY,
    ACTIVE_SOCIAL_CLUB_COOKIE,
    ACTIVE_SOCIAL_CLUB_SESSION_KEY,
    get_club_settings,
    resolve_active_federal_state,
    resolve_active_social_club,
)
from apps.core.authz import staff_or_board_required
from apps.compliance.models import ComplianceReport, SuspiciousActivity
from apps.cultivation.models import GrowCycle, HarvestBatch, Plant
from apps.finance.models import Invoice, Payment
from apps.governance.services import send_due_meeting_notifications
from apps.inventory.models import InventoryCount, InventoryItem, Strain
from apps.members.models import Profile
from apps.orders.models import Order
from apps.participation.models import MemberEngagement, Shift, WorkHours

from .forms import (
    ClubConfigurationForm,
    PublicDocumentForm,
    SocialClubAdminRegistrationForm,
    SocialClubReviewForm,
    SocialClubRegistrationForm,
    SocialClubOpeningHourForm,
    SocialClubSettingsForm,
)
from .models import ClubConfiguration, PublicDocument, SocialClub, SocialClubOpeningHour, SocialClubReview


def _superadmin_required(user: User) -> bool:
    return bool(getattr(user, "is_authenticated", False) and getattr(user, "is_superuser", False))

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
    club_settings = get_club_settings()
    providers = list(club_settings["club_external_services"])
    if django_settings.STRIPE_SECRET_KEY and "Stripe" not in providers:
        providers.append("Stripe fuer Online-Zahlungen und Guthabenaufladungen")
    if django_settings.OPENROUTER_API_KEY and "OpenRouter" not in providers:
        providers.append("OpenRouter fuer optionale KI-gestuetzte Rechnungserkennung")
    if django_settings.GA_TRACKING_ID and "Google Analytics" not in providers:
        providers.append("Google Analytics nach ausdruecklicher Einwilligung")
    return providers


def _legal_setup_complete() -> bool:
    club_settings = get_club_settings()
    required = [
        club_settings["club_name"],
        club_settings["club_contact_address"],
        club_settings["club_contact_email"],
        club_settings["club_board_representatives"],
        club_settings["club_register_court"],
        club_settings["club_tax_number"],
    ]
    return all(bool(value) for value in required)


def _module_links():
    return [
        {
            "title": "Mitglieder-Cockpit",
            "description": "Offene Bewerbungen, Mitgliedsstatus und CSV-Export.",
            "href": reverse("members:directory"),
            "tone": "forest",
        },
        {
            "title": "Bestellungen",
            "description": "Reservierungen pruefen, freigeben oder stornieren.",
            "href": reverse("orders:admin_list"),
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
                        "href": reverse("members:directory"),
                    },
                    {
                        "label": "Reservierte Ausgaben",
                        "value": reserved_orders,
                        "detail": "offene Warenkoerbe mit Reservierung",
                        "tone": "sand",
                        "href": f"{reverse('orders:admin_list')}?status=reserved",
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
            and not profile.is_verified
            and profile.onboarding_complete
        )

    return render(request, "core/dashboard.html", context)


def privacy(request):
    club_settings = get_club_settings(social_club=resolve_active_social_club(request))
    return render(
        request,
        "core/privacy.html",
        {
            "club_service_providers": _configured_service_providers(),
            "legal_setup_complete": _legal_setup_complete(),
            "club_legal_basis_notice": club_settings["club_legal_basis_notice"],
            "club_retention_notice": club_settings["club_retention_notice"],
        },
    )


def imprint(request):
    club_settings = get_club_settings(social_club=resolve_active_social_club(request))
    return render(
        request,
        "core/imprint.html",
        {
            **club_settings,
            "legal_setup_complete": _legal_setup_complete(),
        },
    )


def documents(request):
    active_club = resolve_active_social_club(request)
    documents_qs = PublicDocument.objects.filter(is_public=True)
    if active_club:
        documents_qs = documents_qs.filter(Q(social_club=active_club) | Q(social_club__isnull=True))
    return render(request, "core/documents.html", {"documents": documents_qs})


@require_POST
def switch_social_club(request):
    club = SocialClub.objects.filter(id=request.POST.get("social_club_id"), is_active=True, is_approved=True).first()
    selected_state = (request.POST.get("federal_state") or "").strip()
    valid_states = {code for code, _label in SocialClub.FEDERAL_STATE_CHOICES}
    if selected_state and selected_state not in valid_states:
        messages.error(request, "Bundesland nicht gefunden.")
        return redirect(request.POST.get("next") or "core:dashboard")

    if club:
        if request.user.is_authenticated and not request.user.is_superuser and request.user.social_club_id and request.user.social_club_id != club.id:
            messages.error(request, "Du kannst nur den eigenen Social Club aktivieren.")
            return redirect(request.POST.get("next") or "core:dashboard")
        request.session[ACTIVE_SOCIAL_CLUB_SESSION_KEY] = club.id
    elif request.user.is_authenticated and not request.user.is_superuser and request.user.social_club_id:
        # Keep fixed assignment for non-superusers even if no value was posted.
        request.session[ACTIVE_SOCIAL_CLUB_SESSION_KEY] = request.user.social_club_id

    if selected_state:
        request.session[ACTIVE_FEDERAL_STATE_SESSION_KEY] = selected_state
    else:
        request.session.pop(ACTIVE_FEDERAL_STATE_SESSION_KEY, None)
    request.session.modified = True
    response = redirect(request.POST.get("next") or "core:dashboard")
    if club:
        response.set_cookie(ACTIVE_SOCIAL_CLUB_COOKIE, str(club.id), max_age=60 * 60 * 24 * 365, samesite="Lax")
    if selected_state:
        response.set_cookie(ACTIVE_FEDERAL_STATE_COOKIE, selected_state, max_age=60 * 60 * 24 * 365, samesite="Lax")
    else:
        response.delete_cookie(ACTIVE_FEDERAL_STATE_COOKIE)
    messages.success(request, "Auswahl gespeichert.")
    return response


def pricing(request):
    total_members = Profile.objects.count()
    total_social_clubs = SocialClub.objects.filter(is_active=True).count()
    return render(
        request,
        "core/pricing.html",
        {
            "total_members": total_members,
            "total_social_clubs": total_social_clubs,
            "monthly_price_per_member": "0,25 EUR",
            "one_time_price_per_new_member": "0,50 EUR",
        },
    )


def social_club_public_list(request):
    query = " ".join((request.GET.get("q") or "").split()).strip()
    state_filter = (request.GET.get("federal_state") or resolve_active_federal_state(request) or "").strip()
    price_min = (request.GET.get("price_min") or "").strip()
    price_max = (request.GET.get("price_max") or "").strip()
    valid_states = {code for code, _label in SocialClub.FEDERAL_STATE_CHOICES}
    if state_filter not in valid_states:
        state_filter = ""
    clubs_qs = SocialClub.objects.filter(is_active=True, is_approved=True).order_by("name")
    for club in clubs_qs.filter(slug=""):
        club.save(update_fields=["slug", "updated_at"])
    clubs = SocialClub.objects.filter(is_active=True, is_approved=True).exclude(slug="").order_by("name")
    if state_filter:
        clubs = clubs.filter(federal_state=state_filter)
    if price_min:
        try:
            clubs = clubs.filter(avg_strain_price__gte=Decimal(price_min))
        except Exception:
            price_min = ""
    if price_max:
        try:
            clubs = clubs.filter(avg_strain_price__lte=Decimal(price_max))
        except Exception:
            price_max = ""
    if query:
        clubs = clubs.filter(Q(name__icontains=query) | Q(city__icontains=query))
    return render(
        request,
        "core/social_club_public_list.html",
        {
            "clubs": clubs[:200],
            "query": query,
            "state_filter": state_filter,
            "state_options": SocialClub.FEDERAL_STATE_CHOICES,
            "price_min": price_min,
            "price_max": price_max,
        },
    )


def social_club_regional_list(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        query = " ".join((request.GET.get("q") or "").split()).strip()
        state_filter = (request.GET.get("federal_state") or resolve_active_federal_state(request) or "").strip()
        valid_states = {code for code, _label in SocialClub.FEDERAL_STATE_CHOICES}
        if state_filter not in valid_states:
            state_filter = ""
        clubs = SocialClub.objects.filter(is_active=True, is_approved=True).exclude(slug="").order_by("name")
        if state_filter:
            clubs = clubs.filter(federal_state=state_filter)
        if query:
            clubs = clubs.filter(Q(name__icontains=query) | Q(city__icontains=query))
        clubs = clubs[:200]
        html = render_to_string(
            "core/_social_club_regional_results.html",
            {"clubs": clubs},
            request=request,
        )
        return JsonResponse({"html": html, "count": len(clubs)})

    # Regional page is merged into the main Social-Club listing.
    return social_club_public_list(request)


def social_club_public_detail(request, slug: str):
    club = get_object_or_404(SocialClub, slug=slug, is_active=True, is_approved=True)
    documents = PublicDocument.objects.filter(is_public=True, social_club=club).order_by("display_order", "title")
    statute_documents = documents.filter(category=PublicDocument.CATEGORY_STATUTE)
    reviews = SocialClubReview.objects.filter(social_club=club).select_related("user")[:24]
    review_count = SocialClubReview.objects.filter(social_club=club).count()
    avg_rating = SocialClubReview.objects.filter(social_club=club).aggregate(avg=Sum("rating"))["avg"]
    verified_member_count = Profile.objects.filter(
        user__social_club=club,
        user__role=User.ROLE_MEMBER,
        is_verified=True,
        status=Profile.STATUS_ACTIVE,
    ).count()
    max_verified_members = max(club.max_verified_members or 0, 0)
    verified_member_slots_left = max(max_verified_members - verified_member_count, 0) if max_verified_members else 0
    club_strains = Strain.objects.filter(is_active=True, social_club=club)
    shop_strain_count = club_strains.count()
    shop_strains = list(club_strains.order_by("name").values_list("name", flat=True))
    opening_hours_qs = SocialClubOpeningHour.objects.filter(social_club=club).order_by("weekday", "starts_at", "ends_at")
    weekday_labels = dict(SocialClubOpeningHour.WEEKDAY_CHOICES)
    opening_hours_by_weekday = {weekday: [] for weekday, _label in SocialClubOpeningHour.WEEKDAY_CHOICES}
    for slot in opening_hours_qs:
        opening_hours_by_weekday[slot.weekday].append(slot)
    opening_week_schedule = [
        {
            "weekday": weekday,
            "label": weekday_labels[weekday],
            "slots": opening_hours_by_weekday[weekday],
        }
        for weekday, _label in SocialClubOpeningHour.WEEKDAY_CHOICES
    ]

    return render(
        request,
        "core/social_club_public_detail.html",
        {
            "club": club,
            "documents": documents,
            "statute_documents": statute_documents,
            "reviews": reviews,
            "avg_rating": round(avg_rating, 2) if avg_rating else None,
            "review_count": review_count,
            "verified_member_count": verified_member_count,
            "max_verified_members": max_verified_members,
            "verified_member_slots_left": verified_member_slots_left,
            "shop_strain_count": shop_strain_count,
            "shop_strains": shop_strains,
            "opening_week_schedule": opening_week_schedule,
        },
    )


@login_required
def social_club_review(request):
    profile = Profile.objects.filter(user=request.user).first()
    club = getattr(request.user, "social_club", None)
    eligible = bool(
        request.user.role == User.ROLE_MEMBER
        and request.user.is_active
        and club is not None
        and profile is not None
        and profile.is_verified
        and profile.status == Profile.STATUS_ACTIVE
    )
    if not eligible:
        messages.info(request, "Bewertungen sind nur fuer aktive, verifizierte Mitglieder des eigenen Social Clubs moeglich.")
        return redirect("members:profile")

    review, _ = SocialClubReview.objects.get_or_create(social_club=club, user=request.user, defaults={"rating": 5})
    if request.method == "POST":
        form = SocialClubReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Deine Social-Club-Bewertung wurde gespeichert.")
            return redirect("core:social_club_review")
    else:
        form = SocialClubReviewForm(instance=review)

    recent_reviews = SocialClubReview.objects.filter(social_club=club).select_related("user")[:12]
    avg_rating = round(sum(item.rating for item in recent_reviews) / len(recent_reviews), 2) if recent_reviews else None
    return render(
        request,
        "core/social_club_review.html",
        {
            "club": club,
            "form": form,
            "recent_reviews": recent_reviews,
            "avg_rating": avg_rating,
        },
    )


@staff_or_board_required(_is_staff_or_board)
def documents_admin(request):
    active_club = request.user.social_club if not request.user.is_superuser else resolve_active_social_club(request)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delete":
            document_qs = PublicDocument.objects
            if active_club:
                document_qs = document_qs.filter(social_club=active_club)
            else:
                document_qs = document_qs.filter(social_club__isnull=True)
            document = get_object_or_404(document_qs, pk=request.POST.get("document_id"))
            title = document.title
            document.delete()
            messages.warning(request, f"Dokument {title} wurde geloescht.")
            return redirect("core:documents_admin")
        form = PublicDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            if active_club:
                document.social_club = active_club
            document.save()
            messages.success(request, "Dokument wurde gespeichert.")
            return redirect("core:documents_admin")
    else:
        form = PublicDocumentForm()
    return render(
        request,
        "core/documents_admin.html",
        {
            "form": form,
            "documents": (
                PublicDocument.objects.filter(social_club=active_club).order_by("display_order", "title")
                if active_club
                else PublicDocument.objects.filter(social_club__isnull=True).order_by("display_order", "title")
            ),
        },
    )


@staff_or_board_required(_is_staff_or_board)
def club_settings_admin(request):
    configuration = ClubConfiguration.objects.first() or ClubConfiguration(pk=1)
    if request.method == "POST":
        form = ClubConfigurationForm(request.POST, instance=configuration)
        if form.is_valid():
            form.save()
            messages.success(request, "Club-Konfiguration wurde gespeichert und in der gesamten App aktualisiert.")
            return redirect("core:club_settings")
    else:
        form = ClubConfigurationForm(instance=configuration)
    return render(
        request,
        "core/club_settings.html",
        {
            "form": form,
            "effective_settings": get_club_settings(),
        },
    )


def social_club_register(request):
    session_key = "pending_social_club_id"
    pending_club_id = request.session.get(session_key)
    pending_club = SocialClub.objects.filter(id=pending_club_id, is_approved=False).first() if pending_club_id else None

    if request.method == "POST":
        step = request.POST.get("step", "club")
        if step == "club":
            club_form = SocialClubRegistrationForm(request.POST)
            admin_form = SocialClubAdminRegistrationForm()
            if club_form.is_valid():
                club = club_form.save(commit=False)
                club.is_active = True
                club.is_approved = False
                club.save()
                request.session[session_key] = club.id
                request.session.modified = True
                messages.success(request, "Social Club wurde angelegt. Bitte jetzt den Admin-Zugang erstellen.")
                return redirect("core:social_club_register")
        else:
            club_form = SocialClubRegistrationForm()
            admin_form = SocialClubAdminRegistrationForm(request.POST)
            if not pending_club:
                messages.error(request, "Bitte zuerst den Social Club registrieren.")
                return redirect("core:social_club_register")
            if admin_form.is_valid():
                user = User.objects.create_user(
                    email=admin_form.cleaned_data["email"],
                    password=admin_form.cleaned_data["password"],
                    first_name=admin_form.cleaned_data["first_name"],
                    last_name=admin_form.cleaned_data["last_name"],
                    role=User.ROLE_BOARD,
                    is_staff=True,
                    is_active=False,
                    social_club=pending_club,
                )
                Profile.objects.create(
                    user=user,
                    birth_date=admin_form.cleaned_data["birth_date"],
                    status=Profile.STATUS_PENDING,
                    is_verified=False,
                    monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
                )
                request.session.pop(session_key, None)
                messages.success(
                    request,
                    "Admin-Zugang angelegt. Der Ueberadmin muss Social Club und Admin erst freischalten.",
                )
                return redirect("accounts:login")
    else:
        club_form = SocialClubRegistrationForm()
        admin_form = SocialClubAdminRegistrationForm()

    return render(
        request,
        "core/social_club_register.html",
        {
            "club_form": club_form,
            "admin_form": admin_form,
            "pending_club": pending_club,
        },
    )


@staff_or_board_required(_superadmin_required)
def social_club_admin(request):
    clubs = SocialClub.objects.order_by("is_approved", "name")
    if request.method == "POST":
        club = get_object_or_404(SocialClub, id=request.POST.get("club_id"))
        action = request.POST.get("action")
        if action == "approve":
            club.is_approved = True
            club.is_active = True
            club.save(update_fields=["is_approved", "is_active", "updated_at"])
            club_admins = User.objects.filter(social_club=club, role=User.ROLE_BOARD, is_active=False)
            for admin_user in club_admins:
                admin_user.is_active = True
                admin_user.save(update_fields=["is_active"])
                profile = getattr(admin_user, "profile", None)
                if profile:
                    profile.status = Profile.STATUS_ACTIVE
                    profile.is_verified = True
                    profile.save(update_fields=["status", "is_verified", "updated_at"])
            messages.success(request, f"Social Club {club.name} freigeschaltet.")
        elif action == "deactivate":
            club.is_active = False
            club.save(update_fields=["is_active", "updated_at"])
            messages.warning(request, f"Social Club {club.name} deaktiviert.")
        return redirect("core:social_club_admin")

    return render(
        request,
        "core/social_club_admin.html",
        {
            "clubs": clubs,
            "total_members": Profile.objects.count(),
            "total_social_clubs": SocialClub.objects.count(),
            "approved_social_clubs": SocialClub.objects.filter(is_approved=True).count(),
        },
    )


@staff_or_board_required(_is_staff_or_board)
def social_club_profile(request):
    if request.user.is_superuser:
        club = resolve_active_social_club(request)
    else:
        club = request.user.social_club
    if not club:
        messages.error(request, "Kein Social Club zugeordnet.")
        return redirect("core:dashboard")

    OpeningHourFormSet = inlineformset_factory(
        SocialClub,
        SocialClubOpeningHour,
        form=SocialClubOpeningHourForm,
        extra=1,
        can_delete=True,
    )

    if request.method == "POST":
        form = SocialClubSettingsForm(request.POST, request.FILES, instance=club)
        has_opening_hour_payload = any(key.startswith("opening_hours-") for key in request.POST.keys())
        if has_opening_hour_payload:
            opening_hour_formset = OpeningHourFormSet(request.POST, instance=club, prefix="opening_hours")
            opening_hours_valid = opening_hour_formset.is_valid()
        else:
            opening_hour_formset = OpeningHourFormSet(instance=club, prefix="opening_hours")
            opening_hours_valid = True

        if form.is_valid() and opening_hours_valid:
            form.save()
            if has_opening_hour_payload:
                opening_hour_formset.save()
            messages.success(request, "Social-Club-Daten aktualisiert.")
            return redirect("core:social_club_profile")
    else:
        form = SocialClubSettingsForm(instance=club)
        opening_hour_formset = OpeningHourFormSet(instance=club, prefix="opening_hours")
    return render(
        request,
        "core/social_club_profile.html",
        {"form": form, "club": club, "opening_hour_formset": opening_hour_formset},
    )


@require_POST
def switch_federal_state(request):
    selected_state = (request.POST.get("federal_state") or "").strip()
    valid_states = {code for code, _label in SocialClub.FEDERAL_STATE_CHOICES}
    if selected_state and selected_state not in valid_states:
        messages.error(request, "Bundesland nicht gefunden.")
        return redirect(request.POST.get("next") or "accounts:login")
    if selected_state:
        request.session[ACTIVE_FEDERAL_STATE_SESSION_KEY] = selected_state
    else:
        request.session.pop(ACTIVE_FEDERAL_STATE_SESSION_KEY, None)
    request.session.modified = True
    response = redirect(request.POST.get("next") or "core:social_club_regional_list")
    if selected_state:
        response.set_cookie(ACTIVE_FEDERAL_STATE_COOKIE, selected_state, max_age=60 * 60 * 24 * 365, samesite="Lax")
        messages.success(request, "Bundesland fuer Clubsuche gespeichert.")
    else:
        response.delete_cookie(ACTIVE_FEDERAL_STATE_COOKIE)
        messages.info(request, "Bundesland-Filter zurueckgesetzt.")
    return response

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
