import csv
import io
import re
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from apps.accounts.emails import (
    send_membership_documents_email,
    send_membership_status_email,
    send_registration_received_email,
)
from apps.accounts.models import User
from apps.core.authz import board_required, staff_or_board_required
from apps.finance.models import SepaMandate
from apps.finance.models import Invoice
from apps.messaging.services import sync_member_messaging_preferences
from apps.orders.models import Order
from apps.participation.models import MemberEngagement

from .forms import MemberOnboardingForm, MemberProfileEditForm, MemberRegistrationForm
from .models import Profile

_SEARCH_SANITIZE_RE = re.compile(r"[^0-9A-Za-zÄÖÜäöüß@._+\-\s]")
MEMBER_IMPORT_SESSION_KEY = "member_import_payload"
IMPORT_FIELD_CHOICES = [
    ("", "Nicht importieren"),
    ("email", "E-Mail-Adresse"),
    ("first_name", "Vorname"),
    ("last_name", "Nachname"),
    ("birth_date", "Geburtsdatum"),
    ("desired_join_date", "Aufnahmedatum"),
    ("street_address", "Strasse, Hausnummer"),
    ("postal_code", "Postleitzahl"),
    ("city", "Stadt"),
    ("phone", "Telefonnummer"),
    ("privacy_accepted", "Datenschutzerklaerung"),
    ("iban", "IBAN"),
    ("bic", "BIC"),
    ("bank_name", "Kreditinstitut"),
    ("direct_debit_accepted", "Ermaechtigung zur Lastschrift"),
    ("no_other_csc_membership", "Mitgliedschaft anderer Anbaugemeinschaften"),
    ("german_residence_confirmed", "Fester Wohnsitz in Deutschland"),
    ("minimum_age_confirmed", "Mindestalter 21 Jahre"),
    ("id_document_confirmed", "Aktueller Lichtbildausweis"),
    ("important_newsletter_opt_in", "Newsletter fuer wichtige Ankuendigungen"),
    ("optional_newsletter_opt_in", "Optionaler Newsletter"),
    ("member_number", "Mitgliedsnummer"),
    ("monthly_limit", "Monatsabgabe"),
    ("daily_limit", "Tagesabgabe"),
    ("balance", "Guthaben"),
    ("accepted", "Akzeptiert"),
    ("verified", "Verifiziert"),
]
DEFAULT_IMPORT_MAP = {
    "e-mail-adresse": "email",
    "emailadresse": "email",
    "vorname": "first_name",
    "nachname": "last_name",
    "geburtsdatum": "birth_date",
    "aufnahmedatum": "desired_join_date",
    "strassehausnummer": "street_address",
    "straßehausnummer": "street_address",
    "postleitzahl": "postal_code",
    "stadt": "city",
    "telefonnummer": "phone",
    "datenschutzerklarung": "privacy_accepted",
    "datenschutzerklärung": "privacy_accepted",
    "iban": "iban",
    "bic": "bic",
    "kreditinstitut": "bank_name",
    "ermachtigungzurlastschrift": "direct_debit_accepted",
    "ermächtigungzurlastschrift": "direct_debit_accepted",
    "mitgliedschaftandereranbaugemeinschaften": "no_other_csc_membership",
    "festerwohnsitzindeutschland": "german_residence_confirmed",
    "mindestalter21jahre": "minimum_age_confirmed",
    "aktuellerlichtbildausweis": "id_document_confirmed",
    "newsletterfurwichtigeankundigungen": "important_newsletter_opt_in",
    "newsletterfürwichtigeankündigungen": "important_newsletter_opt_in",
    "optionalernewsletter": "optional_newsletter_opt_in",
    "mitgliedsnummer": "member_number",
    "monatsabgabe": "monthly_limit",
    "tagesabgabe": "daily_limit",
    "guthaben": "balance",
    "akzeptiert": "accepted",
    "verifiziert": "verified",
}


def _is_board(user: User) -> bool:
    return user.is_authenticated and user.role == User.ROLE_BOARD


def _is_staff_or_board(user: User) -> bool:
    return user.is_authenticated and user.role in {User.ROLE_STAFF, User.ROLE_BOARD}


def _sanitize_search_query(raw: str) -> str:
    compact = " ".join(raw.split()).strip()
    sanitized = _SEARCH_SANITIZE_RE.sub("", compact)
    return sanitized[:80].strip()


def _normalize_import_header(value: str) -> str:
    return re.sub(r"[^0-9A-Za-zÄÖÜäöüß]", "", value.strip().lower())


def _suggest_import_mapping(header: str) -> str:
    return DEFAULT_IMPORT_MAP.get(_normalize_import_header(header), "")


def _parse_csv_upload(uploaded_file) -> tuple[list[str], list[dict[str, str]], str]:
    raw_bytes = uploaded_file.read()
    text = raw_bytes.decode("utf-8-sig", errors="replace")
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []
    rows = [{header: (value or "").strip() for header, value in row.items()} for row in reader]
    return headers, rows, text


def _parse_import_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_import_bool(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "ja", "yes", "y", "on"}


def _session_import_data(request):
    return request.session.get(MEMBER_IMPORT_SESSION_KEY) or {}


def _normalize_directory_query(request):
    raw_query = request.GET.get("q", "")
    sanitized_query = _sanitize_search_query(raw_query)
    if raw_query.strip() == sanitized_query:
        return sanitized_query, None
    params = request.GET.copy()
    if sanitized_query:
        params["q"] = sanitized_query
    else:
        params.pop("q", None)
    query_string = params.urlencode()
    target = request.path
    if query_string:
        target = f"{target}?{query_string}"
    return sanitized_query, redirect(target)


def register(request):
    if request.method == "POST":
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_registration_received_email(
                user,
                request,
                is_bootstrap=user.role == User.ROLE_BOARD,
            )
            if user.role == User.ROLE_BOARD:
                messages.success(
                    request,
                    "Erster Systemzugang angelegt. Dieser Account wurde als Vorstand freigeschaltet.",
                )
            else:
                messages.success(
                    request,
                    "Registrierung erfolgreich. Freischaltung folgt nach Verifizierung.",
                )
            return redirect("accounts:login")
    else:
        form = MemberRegistrationForm()
    return render(request, "members/register.html", {"form": form, "is_bootstrap": not User.objects.exists()})


@login_required
def onboarding_view(request):
    profile = get_object_or_404(Profile.objects.select_related("user"), user=request.user)
    engagement = getattr(profile, "engagement", None)
    if profile.onboarding_complete:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = MemberOnboardingForm(request.POST, profile=profile)
        if form.is_valid():
            form.save()
            if request.user.role == User.ROLE_MEMBER:
                send_membership_documents_email(profile, request)
            messages.success(request, "Deine Registrierungsdaten wurden vervollstaendigt.")
            return redirect("core:dashboard")
    else:
        form = MemberOnboardingForm(profile=profile)

    return render(
        request,
        "members/onboarding.html",
        {
            "form": form,
            "profile": profile,
            "engagement": engagement,
        },
    )


@login_required
def profile_view(request):
    profile = get_object_or_404(Profile.objects.select_related("user"), user=request.user)
    if request.method == "POST":
        form = MemberProfileEditForm(request.POST, profile=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Deine Profildaten wurden aktualisiert.")
            return redirect("members:profile")
    else:
        form = MemberProfileEditForm(profile=profile)
    recent_orders = Order.objects.filter(member=request.user).prefetch_related("items__strain").order_by("-created_at")[:8]
    invoices = profile.invoices.order_by("-created_at")[:8]
    payments = profile.payments.select_related("invoice").order_by("-created_at")[:8]
    return render(
        request,
        "members/profile.html",
        {
            "profile": profile,
            "recent_orders": recent_orders,
            "invoices": invoices,
            "payments": payments,
            "is_admin_view": False,
            "can_manage": False,
            "can_view_sensitive_finance": True,
            "show_full_bic": True,
            "show_order_history": True,
            "show_private_profile_details": True,
            "profile_form": form,
            "show_public_directory_link": True,
            "show_profile_edit_callout": True,
            "pending_member_limited_access": profile.status == Profile.STATUS_PENDING,
        },
    )


@login_required
def member_detail(request, profile_id: int):
    profile = get_object_or_404(Profile.objects.select_related("user"), id=profile_id)
    viewer = request.user
    is_admin_view = viewer.role in {User.ROLE_STAFF, User.ROLE_BOARD}
    is_self_view = viewer.id == profile.user_id
    if viewer.role == User.ROLE_MEMBER and not is_self_view:
        messages.info(request, "Mitgliederprofile sind nur fuer Administration und Vorstand verfuegbar.")
        return redirect("core:dashboard")

    recent_orders = (
        Order.objects.filter(member=profile.user).prefetch_related("items__strain").order_by("-created_at")[:12]
        if is_admin_view or is_self_view
        else []
    )
    invoices = profile.invoices.order_by("-created_at")[:12] if is_admin_view or is_self_view else []
    payments = profile.payments.select_related("invoice").order_by("-created_at")[:12] if is_admin_view or is_self_view else []
    return render(
        request,
        "members/profile.html",
        {
            "profile": profile,
            "recent_orders": recent_orders,
            "invoices": invoices,
            "payments": payments,
            "is_admin_view": is_admin_view,
            "can_manage": viewer.role == User.ROLE_BOARD,
            "can_view_sensitive_finance": is_self_view or viewer.role == User.ROLE_BOARD,
            "show_full_bic": is_self_view or viewer.role == User.ROLE_BOARD,
            "show_order_history": is_admin_view or is_self_view,
            "show_private_profile_details": is_admin_view or is_self_view,
            "profile_form": None,
            "show_public_directory_link": True,
            "show_profile_edit_callout": False,
            "pending_member_limited_access": False,
        },
    )


@login_required
def directory(request):
    _, redirect_response = _normalize_directory_query(request)
    if redirect_response:
        return redirect_response
    if request.user.role in {User.ROLE_STAFF, User.ROLE_BOARD}:
        return _staff_directory(request)
    messages.info(request, "Die Mitgliederverwaltung ist nur fuer Administration und Vorstand verfuegbar.")
    return redirect("core:dashboard")


def _staff_directory(request):
    query = _sanitize_search_query(request.GET.get("q", ""))
    status_filter = request.GET.get("status", "").strip()
    locked_filter = request.GET.get("locked", "").strip()

    profiles = (
        Profile.objects.select_related("user")
        .annotate(
            open_invoice_count=Count(
                "invoices",
                filter=Q(invoices__status=Invoice.STATUS_OPEN),
                distinct=True,
            ),
            suspicious_count=Count(
                "suspicious_activities",
                filter=Q(suspicious_activities__is_reported=False),
                distinct=True,
            ),
        )
        .order_by("status", "member_number", "user__last_name", "user__first_name")
    )

    if query:
        query_filter = (
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
        )
        if query.isdigit():
            query_filter |= Q(member_number=int(query))
        profiles = profiles.filter(query_filter)

    if status_filter:
        profiles = profiles.filter(status=status_filter)

    if locked_filter == "yes":
        profiles = profiles.filter(is_locked_for_orders=True)
    elif locked_filter == "no":
        profiles = profiles.filter(is_locked_for_orders=False)

    paginator = Paginator(profiles, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "members/directory.html",
        {
            "page_obj": page_obj,
            "status_choices": Profile.STATUS_CHOICES,
            "filters": {
                "q": query,
                "status": status_filter,
                "locked": locked_filter,
            },
            "can_manage": request.user.role == User.ROLE_BOARD,
        },
    )


def _member_directory(request):
    if request.user.profile.status == Profile.STATUS_PENDING:
        messages.info(request, "Das Mitgliederverzeichnis wird erst nach Freigabe durch den Vorstand sichtbar.")
        return redirect("core:dashboard")
    query = _sanitize_search_query(request.GET.get("q", ""))
    profiles = (
        Profile.objects.select_related("user")
        .filter(status__in=[Profile.STATUS_ACTIVE, Profile.STATUS_VERIFIED])
        .exclude(user=request.user)
        .order_by("user__first_name", "user__last_name")
    )
    if query:
        profiles = profiles.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
        )
    paginator = Paginator(profiles, 24)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "members/directory.html",
        {
            "page_obj": page_obj,
            "status_choices": Profile.STATUS_CHOICES,
            "filters": {"q": query, "status": "", "locked": ""},
            "can_manage": False,
            "is_member_directory": True,
        },
    )


@staff_or_board_required(_is_staff_or_board)
def export_members_csv(request):
    profiles = Profile.objects.select_related("user").order_by("member_number", "user__last_name")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="csc-members.csv"'

    writer = csv.writer(response, delimiter=";")
    writer.writerow(
        [
            "Mitgliedsnummer",
            "Status",
            "Verifiziert",
            "Vorname",
            "Nachname",
            "E-Mail",
            "Rolle",
            "Guthaben",
            "Tagesverbrauch",
            "Monatsverbrauch",
            "Bestellungen gesperrt",
        ]
    )
    for profile in profiles:
        writer.writerow(
            [
                profile.member_number or "",
                profile.get_status_display(),
                "Ja" if profile.is_verified else "Nein",
                profile.user.first_name,
                profile.user.last_name,
                profile.user.email,
                profile.user.get_role_display(),
                profile.balance,
                profile.daily_used,
                profile.monthly_used,
                "Ja" if profile.is_locked_for_orders else "Nein",
            ]
        )
    return response


@staff_or_board_required(_is_staff_or_board)
def import_members_csv(request):
    import_data = _session_import_data(request)
    headers = import_data.get("headers", [])
    preview_rows = import_data.get("preview_rows", [])

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "analyze":
            uploaded_file = request.FILES.get("csv_file")
            if not uploaded_file:
                messages.error(request, "Bitte waehle zuerst eine CSV-Datei aus.")
                return redirect("members:import")
            try:
                headers, rows, raw_text = _parse_csv_upload(uploaded_file)
            except UnicodeDecodeError:
                messages.error(request, "Die CSV-Datei konnte nicht gelesen werden.")
                return redirect("members:import")
            if not headers:
                messages.error(request, "Die CSV-Datei enthaelt keine Kopfzeile.")
                return redirect("members:import")
            request.session[MEMBER_IMPORT_SESSION_KEY] = {
                "filename": uploaded_file.name,
                "headers": headers,
                "preview_rows": rows[:8],
                "raw_text": raw_text,
                "delimiter": ";"
                if ";" in (raw_text.splitlines()[0] if raw_text.splitlines() else "")
                else ",",
            }
            request.session.modified = True
            messages.success(request, "CSV analysiert. Bitte pruefe jetzt die Feldzuordnung.")
            return redirect("members:import")

        if action == "clear":
            request.session.pop(MEMBER_IMPORT_SESSION_KEY, None)
            request.session.modified = True
            messages.info(request, "Importvorschau wurde verworfen.")
            return redirect("members:import")

        if action == "import" and import_data:
            delimiter = import_data.get("delimiter", ",")
            reader = csv.DictReader(io.StringIO(import_data["raw_text"]), delimiter=delimiter)
            mappings = {
                header: request.POST.get(f"mapping_{index}", "")
                for index, header in enumerate(import_data.get("headers", []))
            }
            used_targets = [target for target in mappings.values() if target]
            if "email" not in used_targets:
                messages.error(request, "Mindestens eine Spalte muss auf E-Mail-Adresse gemappt werden.")
                return redirect("members:import")

            created_count = 0
            updated_count = 0
            skipped_rows = []

            for row_index, row in enumerate(reader, start=2):
                mapped = {}
                for header, target in mappings.items():
                    if target:
                        mapped[target] = (row.get(header) or "").strip()
                email = (mapped.get("email") or "").strip().lower()
                birth_date = _parse_import_date(mapped.get("birth_date", ""))
                if not email or not birth_date:
                    skipped_rows.append(f"Zeile {row_index}: E-Mail oder Geburtsdatum fehlt.")
                    continue

                accepted = _parse_import_bool(mapped.get("accepted", ""))
                verified = _parse_import_bool(mapped.get("verified", ""))
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": mapped.get("first_name", ""),
                        "last_name": mapped.get("last_name", ""),
                        "role": User.ROLE_MEMBER,
                    },
                )
                if created:
                    user.set_unusable_password()
                    user.save(update_fields=["password"])
                else:
                    changed_fields = []
                    for field_name in ("first_name", "last_name"):
                        new_value = mapped.get(field_name, "").strip()
                        if new_value and getattr(user, field_name) != new_value:
                            setattr(user, field_name, new_value)
                            changed_fields.append(field_name)
                    if changed_fields:
                        user.save(update_fields=changed_fields)

                target_status = Profile.STATUS_ACTIVE if (accepted or verified) else Profile.STATUS_PENDING
                profile, _ = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        "birth_date": birth_date,
                        "status": target_status,
                        "is_verified": verified,
                        "monthly_counter_key": datetime.now().strftime("%Y-%m"),
                    },
                )
                profile.birth_date = birth_date
                profile.desired_join_date = _parse_import_date(mapped.get("desired_join_date", "")) or profile.desired_join_date
                profile.street_address = mapped.get("street_address", profile.street_address).strip()
                profile.postal_code = mapped.get("postal_code", profile.postal_code).strip()
                profile.city = mapped.get("city", profile.city).strip()
                profile.phone = mapped.get("phone", profile.phone).strip()
                profile.bank_name = mapped.get("bank_name", profile.bank_name).strip()
                profile.account_holder_name = profile.account_holder_name or user.full_name or user.email
                profile.privacy_accepted = _parse_import_bool(mapped.get("privacy_accepted", "")) or profile.privacy_accepted
                profile.direct_debit_accepted = _parse_import_bool(mapped.get("direct_debit_accepted", "")) or profile.direct_debit_accepted
                profile.no_other_csc_membership = _parse_import_bool(mapped.get("no_other_csc_membership", "")) or profile.no_other_csc_membership
                profile.german_residence_confirmed = _parse_import_bool(mapped.get("german_residence_confirmed", "")) or profile.german_residence_confirmed
                profile.minimum_age_confirmed = _parse_import_bool(mapped.get("minimum_age_confirmed", "")) or profile.minimum_age_confirmed
                profile.id_document_confirmed = _parse_import_bool(mapped.get("id_document_confirmed", "")) or profile.id_document_confirmed
                profile.important_newsletter_opt_in = _parse_import_bool(mapped.get("important_newsletter_opt_in", "")) or profile.important_newsletter_opt_in
                profile.optional_newsletter_opt_in = _parse_import_bool(mapped.get("optional_newsletter_opt_in", "")) or profile.optional_newsletter_opt_in
                profile.is_verified = verified or profile.is_verified
                profile.status = target_status
                if mapped.get("member_number", "").isdigit():
                    desired_number = int(mapped["member_number"])
                    conflict = Profile.objects.exclude(pk=profile.pk).filter(member_number=desired_number).exists()
                    if not conflict:
                        profile.member_number = desired_number
                if accepted and not profile.registration_completed_at:
                    profile.registration_completed_at = profile.created_at
                profile.save()

                iban = mapped.get("iban", "").replace(" ", "").upper()
                bic = mapped.get("bic", "").replace(" ", "").upper()
                if iban and bic:
                    mandate = profile.sepa_mandate or SepaMandate.objects.filter(profile=profile, is_active=True).first()
                    if mandate:
                        mandate.iban = iban
                        mandate.bic = bic
                        mandate.account_holder = profile.account_holder_name or user.full_name or user.email
                        mandate.is_active = True
                        mandate.save(update_fields=["iban", "bic", "account_holder", "is_active", "updated_at"])
                    else:
                        mandate = SepaMandate.objects.create(
                            profile=profile,
                            iban=iban,
                            bic=bic,
                            account_holder=profile.account_holder_name or user.full_name or user.email,
                            mandate_reference=f"CSC-IMPORT-{profile.user_id}",
                            is_active=True,
                        )
                    if profile.sepa_mandate_id != mandate.id:
                        profile.sepa_mandate = mandate
                        profile.save(update_fields=["sepa_mandate", "updated_at"])

                engagement, _ = MemberEngagement.objects.get_or_create(profile=profile)
                if profile.registration_completed_at:
                    engagement.registration_completed = True
                    engagement.registration_deadline = None
                    engagement.save(update_fields=["registration_completed", "registration_deadline", "updated_at"])

                sync_member_messaging_preferences(profile)
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            request.session.pop(MEMBER_IMPORT_SESSION_KEY, None)
            request.session.modified = True
            if skipped_rows:
                for item in skipped_rows[:5]:
                    messages.warning(request, item)
            messages.success(
                request,
                f"Import abgeschlossen: {created_count} neu, {updated_count} aktualisiert, {len(skipped_rows)} uebersprungen.",
            )
            return redirect("members:directory")

    suggested_mappings = [
        {"header": header, "value": _suggest_import_mapping(header), "choices": IMPORT_FIELD_CHOICES}
        for header in headers
    ]
    return render(
        request,
        "members/import.html",
        {
            "import_data": import_data,
            "suggested_mappings": suggested_mappings,
            "preview_rows": preview_rows,
        },
    )


@board_required(_is_board)
def member_action(request, profile_id: int):
    profile = get_object_or_404(Profile.objects.select_related("user"), id=profile_id)
    action = request.POST.get("action")
    audit_summary = ""
    next_target = request.POST.get("next") or "members:directory"

    sensitive_actions = {
        "verify",
        "activate",
        "reject",
        "lock_orders",
        "unlock_orders",
        "promote_staff",
        "promote_board",
        "demote_member",
        "delete_member",
    }
    if action in sensitive_actions and request.POST.get("confirm") not in {"yes", "no"}:
        return render(
            request,
            "members/action_confirm.html",
            {
                "profile": profile,
                "action": action,
                "next": next_target,
            },
        )
    if request.POST.get("confirm") == "no":
        messages.info(request, "Die Mitgliederaktion wurde abgebrochen.")
        return redirect(next_target)

    if action == "verify":
        profile.is_verified = True
        profile.status = Profile.STATUS_ACTIVE
        profile.allocate_member_number()
        profile.save(update_fields=["is_verified", "status", "updated_at"])
        sync_member_messaging_preferences(profile)
        send_membership_status_email(
            profile.user,
            request,
            status_title="Mitgliedschaft freigeschaltet",
            message=(
                "Dein Account wurde geprueft und fuer den Clubbetrieb freigeschaltet. "
                "Du kannst jetzt Shop, Bestellungen, Warenkorb und weitere Vereinsfunktionen nutzen."
            ),
            profile=profile,
        )
        messages.success(request, f"Mitglied {profile.user.email} verifiziert und aktiviert.")
        audit_summary = f"Mitglied {profile.user.email} verifiziert."
    elif action == "activate":
        profile.is_verified = True
        profile.status = Profile.STATUS_ACTIVE
        profile.allocate_member_number()
        profile.save(update_fields=["is_verified", "status", "updated_at"])
        sync_member_messaging_preferences(profile)
        send_membership_status_email(
            profile.user,
            request,
            status_title="Mitgliedschaft aktiviert",
            message=(
                "Dein Zugang wurde aktiviert. Du kannst dich jetzt regulaer anmelden und Bestellungen im Shop erfassen."
            ),
            profile=profile,
        )
        messages.success(request, f"Mitglied {profile.user.email} aktiviert.")
        audit_summary = f"Mitglied {profile.user.email} aktiviert."
    elif action == "reject":
        profile.status = Profile.STATUS_REJECTED
        profile.is_verified = False
        profile.save(update_fields=["status", "is_verified", "updated_at"])
        send_membership_status_email(
            profile.user,
            request,
            status_title="Mitgliedschaft abgelehnt",
            message="Deine Registrierung wurde aktuell nicht freigegeben. Bitte melde dich beim Club, falls Rueckfragen offen sind.",
            profile=profile,
        )
        messages.warning(request, f"Mitglied {profile.user.email} wurde abgelehnt.")
        audit_summary = f"Mitglied {profile.user.email} abgelehnt."
    elif action == "lock_orders":
        profile.is_locked_for_orders = True
        profile.save(update_fields=["is_locked_for_orders", "updated_at"])
        messages.warning(request, f"Bestellungen fuer {profile.user.email} wurden gesperrt.")
        audit_summary = f"Bestellsperre fuer {profile.user.email} aktiviert."
    elif action == "unlock_orders":
        profile.is_locked_for_orders = False
        profile.save(update_fields=["is_locked_for_orders", "updated_at"])
        send_membership_status_email(
            profile.user,
            request,
            status_title="Bestellsperre aufgehoben",
            message="Deine Bestellungen wurden wieder freigegeben. Du kannst den Shop wieder normal nutzen.",
            profile=profile,
        )
        messages.success(request, f"Bestellungen fuer {profile.user.email} wurden freigegeben.")
        audit_summary = f"Bestellsperre fuer {profile.user.email} aufgehoben."
    elif action in {"promote_staff", "promote_board", "demote_member"}:
        if profile.user_id == request.user.id and action == "demote_member":
            messages.error(request, "Der eigene Vorstands-Zugang kann hier nicht auf Mitglied zurueckgesetzt werden.")
            return redirect(next_target)
        if action == "promote_staff":
            profile.user.role = User.ROLE_STAFF
            profile.user.is_staff = True
            role_label = "Mitarbeiter"
        elif action == "promote_board":
            profile.user.role = User.ROLE_BOARD
            profile.user.is_staff = True
            role_label = "Vorstand"
        else:
            profile.user.role = User.ROLE_MEMBER
            profile.user.is_staff = False
            role_label = "Mitglied"
        profile.user.save(update_fields=["role", "is_staff"])
        messages.success(request, f"{profile.user.email} wurde als {role_label} gespeichert.")
        audit_summary = f"Rolle fuer {profile.user.email} auf {profile.user.role} gesetzt."
    elif action == "delete_member":
        if profile.user_id == request.user.id:
            messages.error(request, "Der eigene Admin-Zugang kann hier nicht geloescht werden.")
            return redirect(next_target)
        user_email = profile.user.email
        from apps.governance.services import record_audit_event

        record_audit_event(
            actor=request.user,
            domain="members",
            action="deleted",
            target=profile,
            summary=f"Mitglied {user_email} wurde geloescht.",
            metadata={"status": profile.status},
            request=request,
        )
        profile.user.delete()
        messages.warning(request, f"Mitglied {user_email} wurde geloescht.")
        return redirect("members:directory")
    else:
        messages.error(request, "Unbekannte Aktion.")

    if audit_summary:
        from apps.governance.services import record_audit_event

        record_audit_event(
            actor=request.user,
            domain="members",
            action=action,
            target=profile,
            summary=audit_summary,
            metadata={
                "status": profile.status,
                "locked_for_orders": profile.is_locked_for_orders,
                "role": profile.user.role,
            },
            request=request,
        )

    return redirect(next_target)


@board_required(_is_board)
def verify_member(request, profile_id: int):
    request.POST = request.POST.copy()
    request.POST["action"] = "verify"
    return member_action(request, profile_id)
