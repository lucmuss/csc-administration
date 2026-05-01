from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_orderitem_batch"),
        ("inventory", "0009_alter_batch_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                (
                    "kind",
                    models.CharField(
                        choices=[("reservation", "Reservierung"), ("release", "Freigabe"), ("sale", "Verkauf")],
                        default="reservation",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inventory_transactions",
                        to="inventory.batch",
                    ),
                ),
                (
                    "order_item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inventory_transactions",
                        to="orders.orderitem",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
