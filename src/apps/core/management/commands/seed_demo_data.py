import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from apps.accounts.models import User
from apps.compliance.models import PreventionInfo
from apps.finance.models import Invoice, Payment, Reminder, SepaMandate
from apps.governance.models import MemberCard
from apps.inventory.models import Batch, InventoryCount, InventoryItem, InventoryLocation, Strain
from apps.members.models import Profile
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

            refs = {}
            self._seed_users(users_data, refs)
            self._seed_catalog(catalog_data, refs)
            self._seed_activity(activity_data, refs)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data seeded: "
                f"{User.objects.count()} users, "
                f"{Strain.objects.count()} strains, "
                f"{Order.objects.count()} orders, "
                f"{Invoice.objects.count()} invoices."
            )
        )

    def _read_json(self, path: Path):
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _reset(self):
        self._safe_delete(OrderItem)
        self._safe_delete(PreventionInfo)
        self._safe_delete(Payment)
        self._safe_delete(Reminder)
        self._safe_delete(Invoice)
        self._safe_delete(Order)
        self._safe_delete(InventoryCount)
        self._safe_delete(InventoryItem)
        self._safe_delete(Batch)
        self._safe_delete(InventoryLocation)
        self._safe_delete(Strain)
        self._safe_delete(WorkHours)
        self._safe_delete(Shift)
        self._safe_delete(MemberCard)
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
                },
            )
            user.first_name = entry["first_name"]
            user.last_name = entry["last_name"]
            user.role = entry.get("role", User.ROLE_MEMBER)
            user.is_staff = entry.get("is_staff", False)
            user.is_superuser = entry.get("is_superuser", False)
            user.is_active = entry.get("is_active", True)
            user.set_password(entry.get("password") or default_password)
            user.save()

            profile_data = entry.get("profile", {})
            profile, _ = Profile.objects.update_or_create(
                user=user,
                defaults={
                    "birth_date": _parse_date(profile_data["birth_date"]),
                    "member_number": profile_data.get("member_number"),
                    "status": profile_data.get("status", Profile.STATUS_PENDING),
                    "is_verified": profile_data.get("is_verified", False),
                    "balance": _parse_decimal(profile_data.get("balance")),
                    "is_locked_for_orders": profile_data.get("is_locked_for_orders", False),
                    "daily_used": _parse_decimal(profile_data.get("daily_used")),
                    "monthly_used": _parse_decimal(profile_data.get("monthly_used")),
                    "daily_counter_date": timezone.localdate(),
                    "monthly_counter_key": month_key,
                    "last_activity": _parse_datetime(profile_data.get("last_activity")),
                    "work_hours_done": _parse_decimal(profile_data.get("work_hours_done")),
                },
            )

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
            InventoryCount.objects.update_or_create(
                date=_parse_date(entry["date"]),
                defaults={
                    "items_counted": entry.get("items_counted", 0),
                    "discrepancies": entry.get("discrepancies", []),
                },
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
