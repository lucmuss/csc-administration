import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime, parse_time

from apps.accounts.models import User
from apps.audit.models import AuditLog as SystemAuditLog
from apps.compliance.models import ComplianceReport, PreventionInfo
from apps.core.models import SocialClub, SocialClubOpeningHour
from apps.finance.models import BalanceTopUp, BalanceTransaction, Invoice, Payment, Reminder, SepaMandate, UploadedInvoice
from apps.finance.services import add_balance_transaction, ensure_seed_credit, import_uploaded_invoices_from_directory, sync_profile_balance
from apps.governance.models import AuditLog as GovernanceAuditLog
from apps.governance.models import BoardMeeting, BoardTask, MeetingAgendaItem, MeetingResolution, MemberCard
from apps.inventory.models import Batch, InventoryCount, InventoryItem, InventoryLocation, Strain
from apps.members.models import Profile, VerificationSubmission
from apps.messaging.models import EmailGroup, EmailGroupMember, EmailTemplate
from apps.orders.models import Order, OrderItem
from apps.participation.models import MemberEngagement, Shift, WorkHours


def _parse_decimal(value, default: str = "0.00") -> Decimal:
    if value in (None, ""):
        return Decimal(default)
    return Decimal(str(value))


def _parse_date(value):
    if not value:
        return None
    parsed = parse_date(value)
    if parsed is None:
        raise ValueError(f"Invalid date value: {value}")
    return parsed


def _parse_datetime(value):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        raise ValueError(f"Invalid datetime value: {value}")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _parse_time(value):
    if not value:
        return None
    parsed = parse_time(value)
    if parsed is None:
        raise ValueError(f"Invalid time value: {value}")
    return parsed


class Command(BaseCommand):
    help = "Seeds reproducible demo data for dashboard, catalog, orders and finance."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo-related data before seeding.")

    def handle(self, *args, **options):
        self._tables = set(connection.introspection.table_names())
        if options["reset"]:
            self._reset()

        with transaction.atomic():
            data_dir = Path(settings.BASE_DIR) / "data"
            users_data = self._read_json(data_dir / "users.json")
            catalog_data = self._read_json(data_dir / "catalog.json")
            activity_data = self._read_json(data_dir / "activity.json")
            social_clubs_data = self._read_json(data_dir / "social_clubs.json")
            governance_data = self._read_json(data_dir / "governance.json")
            messaging_data = self._read_json(data_dir / "messaging.json")

            refs = {}
            self._seed_social_clubs(social_clubs_data, refs)
            self._seed_users(users_data, refs)
            self._seed_catalog(catalog_data, refs)
            self._seed_activity(activity_data, refs)
            self._seed_governance(governance_data, refs)
            self._seed_messaging(messaging_data, refs)
            self._seed_invoice_archive(data_dir / "invoices", refs)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data seeded: "
                f"{User.objects.count()} users, "
                f"{Strain.objects.count()} strains, "
                f"{Order.objects.count()} orders, "
                f"{Invoice.objects.count()} invoices, "
                f"{UploadedInvoice.objects.count()} archive documents."
            )
        )

    def _read_json(self, path: Path):
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _reset(self):
        self._safe_delete(MeetingResolution)
        self._safe_delete(MeetingAgendaItem)
        self._safe_delete(BoardTask)
        self._safe_delete(BoardMeeting)
        self._safe_delete(ComplianceReport)
        self._safe_delete(SystemAuditLog)
        self._safe_delete(GovernanceAuditLog)
        self._safe_delete(EmailGroupMember)
        self._safe_delete(EmailTemplate)
        self._safe_delete(EmailGroup)
        self._safe_delete(OrderItem)
        self._safe_delete(PreventionInfo)
        self._safe_delete(Payment)
        self._safe_delete(Reminder)
        self._safe_delete(Invoice)
        self._safe_delete(BalanceTopUp)
        self._safe_delete(UploadedInvoice)
        self._safe_delete(BalanceTransaction)
        self._safe_delete(Order)
        self._safe_delete(InventoryCount)
        self._safe_delete(InventoryItem)
        self._safe_delete(Batch)
        self._safe_delete(InventoryLocation)
        self._safe_delete(Strain)
        self._safe_delete(WorkHours)
        self._safe_delete(Shift)
        self._safe_delete(MemberCard)
        self._safe_delete(VerificationSubmission)
        if self._table_ready(Profile):
            Profile.objects.update(sepa_mandate=None)
        self._safe_delete(SepaMandate)
        self._safe_delete(MemberEngagement)
        self._safe_delete(Profile)
        self._safe_delete(User)

    def _table_ready(self, model) -> bool:
        return model._meta.db_table in self._tables

    def _safe_delete(self, model) -> None:
        if self._table_ready(model):
            table_name = connection.ops.quote_name(model._meta.db_table)
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {table_name}")

    def _seed_users(self, data, refs):
        default_password = data.get("default_password", "StrongPass123!")
        month_key = timezone.localdate().strftime("%Y-%m")

        for entry in data.get("users", []):
            user, created = User.objects.get_or_create(
                email=entry["email"],
                defaults={
                    "first_name": entry["first_name"],
                    "last_name": entry["last_name"],
                    "role": entry.get("role", User.ROLE_MEMBER),
                    "is_staff": entry.get("is_staff", False),
                    "is_superuser": entry.get("is_superuser", False),
                    "is_active": entry.get("is_active", True),
                    "social_club": refs.get(f"club:{entry.get('social_club')}") if entry.get("social_club") else None,
                },
            )
            user.first_name = entry["first_name"]
            user.last_name = entry["last_name"]
            user.role = entry.get("role", User.ROLE_MEMBER)
            user.is_staff = entry.get("is_staff", False)
            user.is_superuser = entry.get("is_superuser", False)
            user.is_active = entry.get("is_active", True)
            if entry.get("social_club"):
                user.social_club = refs.get(f"club:{entry['social_club']}")
            user.set_password(entry.get("password") or default_password)
            user.save()

            profile_data = entry.get("profile", {})
            target_balance = _parse_decimal(profile_data.get("balance"))
            profile, _ = Profile.objects.update_or_create(
                user=user,
                defaults={
                    "birth_date": _parse_date(profile_data["birth_date"]),
                    "member_number": profile_data.get("member_number"),
                    "status": profile_data.get("status", Profile.STATUS_PENDING),
                    "is_verified": profile_data.get("is_verified", False),
                    "balance": Decimal("0.00"),
                    "is_locked_for_orders": profile_data.get("is_locked_for_orders", False),
                    "daily_used": _parse_decimal(profile_data.get("daily_used")),
                    "monthly_used": _parse_decimal(profile_data.get("monthly_used")),
                    "daily_counter_date": timezone.localdate(),
                    "monthly_counter_key": month_key,
                    "last_activity": _parse_datetime(profile_data.get("last_activity")),
                    "work_hours_done": _parse_decimal(profile_data.get("work_hours_done")),
                },
            )

            ensure_seed_credit(profile, Decimal("100.00"))
            balance_delta = target_balance
            if balance_delta != Decimal("0.00"):
                reference = f"seed-balance-adjustment-{user.email}"
                if not BalanceTransaction.objects.filter(profile=profile, reference=reference).exists():
                    add_balance_transaction(
                        profile=profile,
                        amount=balance_delta,
                        kind=BalanceTransaction.KIND_MANUAL_ADJUSTMENT,
                        note="Bestehendes Seed-Guthaben",
                        reference=reference,
                    )
            sync_profile_balance(profile)

            engagement_data = entry.get("engagement")
            if engagement_data:
                MemberEngagement.objects.update_or_create(
                    profile=profile,
                    defaults={
                        "required_hours_year": _parse_decimal(engagement_data.get("required_hours_year"), "20.00"),
                        "annual_meeting_date": _parse_date(engagement_data.get("annual_meeting_date")),
                        "registration_deadline": _parse_date(engagement_data.get("registration_deadline")),
                        "registration_completed": engagement_data.get("registration_completed", False),
                    },
                )

            card_data = entry.get("card")
            if card_data and self._table_ready(MemberCard):
                MemberCard.objects.update_or_create(
                    profile=profile,
                    defaults={
                        "card_number": card_data["card_number"],
                        "status": card_data.get("status", MemberCard.STATUS_ACTIVE),
                        "notes": card_data.get("notes", ""),
                        "issued_by": user if user.is_staff else None,
                    },
                )

            mandate_data = entry.get("sepa_mandate")
            if mandate_data:
                mandate, _ = SepaMandate.objects.update_or_create(
                    mandate_reference=mandate_data["mandate_reference"],
                    defaults={
                        "profile": profile,
                        "iban": mandate_data["iban"],
                        "bic": mandate_data["bic"],
                        "account_holder": mandate_data["account_holder"],
                        "is_active": mandate_data.get("is_active", True),
                        "signed_at": timezone.now(),
                    },
                )
                if profile.sepa_mandate_id != mandate.id:
                    profile.sepa_mandate = mandate
                    profile.save(update_fields=["sepa_mandate", "updated_at"])

            refs[entry["key"]] = {
                "user": user,
                "profile": profile,
            }

    def _seed_social_clubs(self, data, refs):
        for entry in data.get("social_clubs", []):
            club, _ = SocialClub.objects.update_or_create(
                name=entry["name"],
                defaults={
                    "email": entry["email"],
                    "street_address": entry["street_address"],
                    "postal_code": entry["postal_code"],
                    "city": entry["city"],
                    "federal_state": entry.get("federal_state", ""),
                    "phone": entry["phone"],
                    "website": entry.get("website", ""),
                    "public_description": entry.get("public_description", ""),
                    "membership_email": entry.get("membership_email", ""),
                    "support_email": entry.get("support_email", ""),
                    "prevention_email": entry.get("prevention_email", ""),
                    "finance_email": entry.get("finance_email", ""),
                    "privacy_contact": entry.get("privacy_contact", ""),
                    "data_protection_officer": entry.get("data_protection_officer", ""),
                    "is_active": entry.get("is_active", True),
                    "is_approved": entry.get("is_approved", True),
                },
            )
            refs[f"club:{entry['key']}"] = club

            SocialClubOpeningHour.objects.filter(social_club=club).delete()
            for slot in entry.get("opening_hours", []):
                SocialClubOpeningHour.objects.create(
                    social_club=club,
                    weekday=slot["weekday"],
                    starts_at=_parse_time(slot["starts_at"]),
                    ends_at=_parse_time(slot["ends_at"]),
                )

    def _seed_catalog(self, data, refs):
        for entry in data.get("locations", []):
            location, _ = InventoryLocation.objects.update_or_create(
                name=entry["name"],
                defaults={
                    "type": entry.get("type", InventoryLocation.TYPE_SHELF),
                    "capacity": _parse_decimal(entry.get("capacity")),
                },
            )
            refs[entry["key"]] = location

        for entry in data.get("strains", []):
            strain, _ = Strain.objects.update_or_create(
                name=entry["name"],
                defaults={
                    "thc": _parse_decimal(entry.get("thc")),
                    "cbd": _parse_decimal(entry.get("cbd")),
                    "price": _parse_decimal(entry.get("price")),
                    "stock": _parse_decimal(entry.get("stock")),
                    "product_type": entry.get("product_type", Strain.PRODUCT_TYPE_FLOWER),
                    "card_tone": entry.get("card_tone", Strain.CARD_TONE_APRICOT),
                    "quality_grade": entry.get("quality_grade", Strain.QUALITY_B),
                    "is_active": entry.get("is_active", True),
                },
            )
            refs[entry["key"]] = strain

        for entry in data.get("inventory_items", []):
            InventoryItem.objects.update_or_create(
                strain=refs[entry["strain"]],
                location=refs[entry["location"]],
                defaults={
                    "quantity": _parse_decimal(entry.get("quantity")),
                    "last_counted": _parse_date(entry.get("last_counted")),
                },
            )

        for entry in data.get("batches", []):
            batch, _ = Batch.objects.update_or_create(
                code=entry["code"],
                defaults={
                    "strain": refs[entry["strain"]],
                    "quantity": _parse_decimal(entry.get("quantity")),
                    "harvested_at": _parse_date(entry.get("harvested_at")),
                    "is_active": entry.get("is_active", True),
                },
            )
            refs[entry["key"]] = batch

    def _seed_activity(self, data, refs):
        for entry in data.get("inventory_counts", []):
            count_date = _parse_date(entry["date"])
            existing_counts = InventoryCount.objects.filter(date=count_date).order_by("id")
            inventory_count = existing_counts.first()
            if inventory_count:
                if existing_counts.count() > 1:
                    existing_counts.exclude(id=inventory_count.id).delete()
                inventory_count.items_counted = entry.get("items_counted", 0)
                inventory_count.discrepancies = entry.get("discrepancies", [])
                inventory_count.save(update_fields=["items_counted", "discrepancies"])
            else:
                InventoryCount.objects.create(
                    date=count_date,
                    items_counted=entry.get("items_counted", 0),
                    discrepancies=entry.get("discrepancies", []),
                )

        for entry in data.get("shifts", []):
            shift, _ = Shift.objects.update_or_create(
                title=entry["title"],
                starts_at=_parse_datetime(entry["starts_at"]),
                defaults={
                    "description": entry.get("description", ""),
                    "ends_at": _parse_datetime(entry["ends_at"]),
                    "required_members": entry.get("required_members", 1),
                },
            )
            refs[f"shift:{entry['title']}"] = shift

        for entry in data.get("work_hours", []):
            profile = refs[entry["member"]]["profile"]
            WorkHours.objects.update_or_create(
                profile=profile,
                shift=refs.get(f"shift:{entry['shift']}"),
                date=_parse_date(entry["date"]),
                defaults={
                    "hours": _parse_decimal(entry.get("hours")),
                    "approved": entry.get("approved", False),
                    "notes": entry.get("notes", ""),
                },
            )

        for entry in data.get("orders", []):
            order = self._upsert_order(entry, refs)

            prevention_info = entry.get("prevention_info")
            if prevention_info:
                PreventionInfo.objects.update_or_create(
                    profile=refs[entry["member"]]["profile"],
                    defaults={
                        "first_order": order,
                        "info_version": prevention_info.get("info_version", "CanG-2024"),
                        "notes": prevention_info.get("notes", ""),
                    },
                )

    def _seed_invoice_archive(self, directory: Path, refs) -> None:
        seed_user = (
            refs.get("board", {}).get("user")
            or refs.get("admin", {}).get("user")
            or User.objects.filter(role__in=[User.ROLE_BOARD, User.ROLE_STAFF]).order_by("id").first()
        )
        import_uploaded_invoices_from_directory(
            directory=directory,
            created_by=seed_user,
            assigned_to=seed_user,
            analyze=True,
        )

    def _seed_governance(self, data, refs):
        for entry in data.get("meetings", []):
            chair = refs.get(entry.get("chair"), {}).get("user") if entry.get("chair") else None
            creator = refs.get(entry.get("created_by"), {}).get("user") if entry.get("created_by") else None
            meeting, _ = BoardMeeting.objects.update_or_create(
                title=entry["title"],
                scheduled_for=_parse_datetime(entry["scheduled_for"]),
                defaults={
                    "meeting_type": entry.get("meeting_type", BoardMeeting.TYPE_BOARD),
                    "status": entry.get("status", BoardMeeting.STATUS_PLANNED),
                    "location": entry.get("location", ""),
                    "minutes_summary": entry.get("minutes_summary", ""),
                    "chairperson": chair,
                    "created_by": creator,
                },
            )
            refs[f"meeting:{entry['key']}"] = meeting

            for item in entry.get("agenda_items", []):
                owner = refs.get(item.get("owner"), {}).get("user") if item.get("owner") else None
                agenda_item, _ = MeetingAgendaItem.objects.update_or_create(
                    meeting=meeting,
                    order=item["order"],
                    defaults={
                        "title": item["title"],
                        "description": item.get("description", ""),
                        "status": item.get("status", MeetingAgendaItem.STATUS_OPEN),
                        "owner": owner,
                    },
                )
                refs[f"agenda:{entry['key']}:{item['order']}"] = agenda_item

            for resolution in entry.get("resolutions", []):
                agenda_ref = f"agenda:{entry['key']}:{resolution.get('agenda_order')}"
                meeting_agenda = refs.get(agenda_ref)
                resolution_creator = refs.get(resolution.get("created_by"), {}).get("user") if resolution.get("created_by") else None
                MeetingResolution.objects.update_or_create(
                    meeting=meeting,
                    title=resolution["title"],
                    defaults={
                        "agenda_item": meeting_agenda,
                        "decision_text": resolution["decision_text"],
                        "status": resolution.get("status", MeetingResolution.STATUS_DRAFT),
                        "vote_result": resolution.get("vote_result", ""),
                        "created_by": resolution_creator,
                    },
                )

        for entry in data.get("tasks", []):
            owner = refs.get(entry.get("owner"), {}).get("user") if entry.get("owner") else None
            creator = refs.get(entry.get("created_by"), {}).get("user") if entry.get("created_by") else None
            related_meeting = refs.get(f"meeting:{entry.get('meeting')}") if entry.get("meeting") else None
            BoardTask.objects.update_or_create(
                title=entry["title"],
                defaults={
                    "description": entry.get("description", ""),
                    "status": entry.get("status", BoardTask.STATUS_TODO),
                    "priority": entry.get("priority", BoardTask.PRIORITY_MEDIUM),
                    "due_date": _parse_date(entry.get("due_date")),
                    "owner": owner,
                    "created_by": creator,
                    "related_meeting": related_meeting,
                },
            )

    def _seed_messaging(self, data, refs):
        for entry in data.get("email_groups", []):
            creator = refs.get(entry.get("created_by"), {}).get("user") if entry.get("created_by") else None
            group, _ = EmailGroup.objects.update_or_create(
                name=entry["name"],
                defaults={
                    "description": entry.get("description", ""),
                    "is_active": entry.get("is_active", True),
                    "created_by": creator,
                },
            )
            refs[f"email_group:{entry['key']}"] = group

            for member_key in entry.get("members", []):
                member_ref = refs.get(member_key)
                if member_ref:
                    EmailGroupMember.objects.get_or_create(
                        group=group,
                        member=member_ref["profile"],
                        defaults={"added_by": creator},
                    )

        for entry in data.get("email_templates", []):
            EmailTemplate.objects.update_or_create(
                slug=entry["slug"],
                defaults={
                    "name": entry["name"],
                    "subject": entry["subject"],
                    "body": entry["body"],
                },
            )

    def _upsert_order(self, entry, refs):
        member = refs[entry["member"]]["user"]
        profile = refs[entry["member"]]["profile"]
        invoice_data = entry["invoice"]
        existing_invoice = Invoice.objects.filter(invoice_number=invoice_data["invoice_number"]).select_related("order").first()

        if existing_invoice and existing_invoice.order:
            order = existing_invoice.order
            order.member = member
            order.status = entry.get("status", Order.STATUS_RESERVED)
            order.reserved_until = _parse_datetime(entry["reserved_until"])
            order.paid_with_balance = _parse_decimal(entry.get("paid_with_balance"))
            order.total = _parse_decimal(entry.get("total"))
            order.total_grams = _parse_decimal(entry.get("total_grams"))
            order.save()
            order.items.all().delete()
        else:
            order = Order.objects.create(
                member=member,
                status=entry.get("status", Order.STATUS_RESERVED),
                reserved_until=_parse_datetime(entry["reserved_until"]),
                paid_with_balance=_parse_decimal(entry.get("paid_with_balance")),
                total=_parse_decimal(entry.get("total")),
                total_grams=_parse_decimal(entry.get("total_grams")),
            )

        for item in entry.get("items", []):
            OrderItem.objects.create(
                order=order,
                strain=refs[item["strain"]],
                batch=refs.get(item.get("batch")),
                quantity_grams=_parse_decimal(item.get("quantity_grams")),
                unit_price=_parse_decimal(item.get("unit_price")),
                total_price=_parse_decimal(item.get("total_price")),
            )

        invoice, _ = Invoice.objects.update_or_create(
            invoice_number=invoice_data["invoice_number"],
            defaults={
                "profile": profile,
                "order": order,
                "amount": _parse_decimal(invoice_data.get("amount")),
                "due_date": _parse_date(invoice_data["due_date"]),
                "status": invoice_data.get("status", Invoice.STATUS_OPEN),
                "reminder_level": invoice_data.get("reminder_level", 0),
                "blocked_member": invoice_data.get("blocked_member", False),
            },
        )

        invoice.payments.all().delete()
        for payment_data in invoice_data.get("payments", []):
            Payment.objects.create(
                invoice=invoice,
                profile=profile,
                mandate=profile.sepa_mandate,
                amount=_parse_decimal(payment_data.get("amount")),
                method=payment_data.get("method", Payment.METHOD_SEPA),
                status=payment_data.get("status", Payment.STATUS_PENDING),
                scheduled_for=_parse_date(payment_data.get("scheduled_for")) or timezone.localdate(),
            )

        invoice.reminders.all().delete()
        for reminder_data in invoice_data.get("reminders", []):
            Reminder.objects.create(
                invoice=invoice,
                level=reminder_data["level"],
                fee_amount=_parse_decimal(reminder_data.get("fee_amount")),
                note=reminder_data.get("note", ""),
            )

        return order
