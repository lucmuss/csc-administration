from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0006_profile_onboarding_extended_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("finance", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BalanceTopUp",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(default="stripe", max_length=16)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="eur", max_length=8)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Ausstehend"),
                            ("completed", "Abgeschlossen"),
                            ("failed", "Fehlgeschlagen"),
                            ("expired", "Abgelaufen"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("checkout_session_id", models.CharField(blank=True, max_length=255, unique=True)),
                ("checkout_url", models.URLField(blank=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("failure_reason", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="balance_topups", to="members.profile"),
                ),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="BalanceTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("membership_fee", "Mitgliedsbeitrag"),
                            ("topup", "Aufladung"),
                            ("manual_adjustment", "Manuelle Anpassung"),
                            ("order_charge", "Bestellung belastet"),
                            ("order_refund", "Bestellung erstattet"),
                        ],
                        max_length=32,
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=255)),
                ("reference", models.CharField(blank=True, db_index=True, max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_balance_transactions", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "profile",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="balance_transactions", to="members.profile"),
                ),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
