from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("finance", "0002_balancetransaction_balancetopup"),
    ]

    operations = [
        migrations.CreateModel(
            name="UploadedInvoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                (
                    "direction",
                    models.CharField(
                        choices=[("incoming", "Eingangsrechnung"), ("outgoing", "Ausgangsrechnung")],
                        default="incoming",
                        max_length=16,
                    ),
                ),
                ("document", models.FileField(upload_to="finance/invoices/")),
                ("invoice_number", models.CharField(blank=True, max_length=120)),
                ("vendor_name", models.CharField(blank=True, max_length=180)),
                ("customer_name", models.CharField(blank=True, max_length=180)),
                ("issue_date", models.DateField(blank=True, null=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("amount_net", models.DecimalField(decimal_places=2, default="0.00", max_digits=10)),
                ("amount_tax", models.DecimalField(decimal_places=2, default="0.00", max_digits=10)),
                ("amount_gross", models.DecimalField(decimal_places=2, default="0.00", max_digits=10)),
                ("currency", models.CharField(default="EUR", max_length=8)),
                (
                    "payment_status",
                    models.CharField(
                        choices=[("open", "Offen"), ("paid", "Bezahlt"), ("cancelled", "Storniert")],
                        default="open",
                        max_length=16,
                    ),
                ),
                ("paid_at", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("ai_summary", models.TextField(blank=True)),
                ("ai_payload", models.JSONField(blank=True, default=dict)),
                (
                    "extraction_status",
                    models.CharField(
                        choices=[("pending", "Ausstehend"), ("success", "Erkannt"), ("failed", "Pruefen")],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("extraction_error", models.CharField(blank=True, max_length=255)),
                ("extracted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_uploaded_invoices",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_uploaded_invoices",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-issue_date", "-created_at", "-id"]},
        ),
    ]
