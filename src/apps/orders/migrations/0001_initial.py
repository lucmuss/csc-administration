from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("inventory", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("reserved", "Reserviert"), ("completed", "Abgeschlossen"), ("cancelled", "Storniert")], default="reserved", max_length=20)),
                ("total", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("total_grams", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=8)),
                ("reserved_until", models.DateTimeField()),
                ("paid_with_balance", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity_grams", models.DecimalField(decimal_places=2, max_digits=8)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("total_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.order")),
                ("strain", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="inventory.strain")),
            ],
            options={"ordering": ["id"]},
        ),
    ]
