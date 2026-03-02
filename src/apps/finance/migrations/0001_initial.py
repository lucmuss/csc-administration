# Generated manually for finance app.
from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("members", "0001_initial"),
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SepaMandate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("iban", models.CharField(max_length=34)),
                ("bic", models.CharField(max_length=11)),
                ("account_holder", models.CharField(max_length=255)),
                ("mandate_reference", models.CharField(max_length=64, unique=True)),
                ("signed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sepa_mandates",
                        to="members.profile",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("invoice_number", models.CharField(max_length=32, unique=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("due_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Offen"), ("paid", "Bezahlt"), ("cancelled", "Storniert")],
                        default="open",
                        max_length=16,
                    ),
                ),
                ("reminder_level", models.PositiveSmallIntegerField(default=0)),
                ("blocked_member", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "order",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="invoice",
                        to="orders.order",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invoices",
                        to="members.profile",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "method",
                    models.CharField(
                        choices=[("balance", "Guthaben"), ("sepa", "SEPA")], default="sepa", max_length=16
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Ausstehend"),
                            ("pre_notified", "Vorabankuendigung gesendet"),
                            ("collected", "Eingezogen"),
                            ("returned", "Ruecklaeufer"),
                            ("failed", "Fehlgeschlagen"),
                        ],
                        default="pending",
                        max_length=24,
                    ),
                ),
                ("scheduled_for", models.DateField(default=django.utils.timezone.localdate)),
                ("prenotified_at", models.DateTimeField(blank=True, null=True)),
                ("collected_at", models.DateTimeField(blank=True, null=True)),
                ("returned_at", models.DateTimeField(blank=True, null=True)),
                ("failure_reason", models.CharField(blank=True, max_length=255)),
                ("sepa_batch_id", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="finance.invoice",
                    ),
                ),
                (
                    "mandate",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="payments",
                        to="finance.sepamandate",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="members.profile",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Reminder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "level",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Erinnerung"), (2, "1. Mahnung"), (3, "2. Mahnung"), (4, "3. Mahnung")]
                    ),
                ),
                ("fee_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=8)),
                ("sent_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("note", models.CharField(blank=True, max_length=255)),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reminders",
                        to="finance.invoice",
                    ),
                ),
            ],
            options={"ordering": ["-sent_at"], "unique_together": {("invoice", "level")}},
        ),
    ]
