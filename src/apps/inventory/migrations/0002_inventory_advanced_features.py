from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="strain",
            name="quality_grade",
            field=models.CharField(
                choices=[("A+", "A+"), ("A", "A"), ("B", "B"), ("C", "C")],
                default="B",
                max_length=2,
            ),
        ),
        migrations.CreateModel(
            name="InventoryLocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                (
                    "type",
                    models.CharField(
                        choices=[("dry_room", "Trockenraum"), ("vault", "Tresor"), ("shelf", "Regal")],
                        default="shelf",
                        max_length=20,
                    ),
                ),
                ("capacity", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="InventoryCount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("items_counted", models.PositiveIntegerField(default=0)),
                ("discrepancies", models.JSONField(blank=True, default=list)),
            ],
            options={"ordering": ["-date", "-id"]},
        ),
        migrations.CreateModel(
            name="Batch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("quantity", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("harvested_at", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "strain",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="batches", to="inventory.strain"),
                ),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.CreateModel(
            name="InventoryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("last_counted", models.DateField(blank=True, null=True)),
                (
                    "location",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="inventory.inventorylocation"),
                ),
                (
                    "strain",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_items", to="inventory.strain"),
                ),
            ],
            options={"ordering": ["location__name", "strain__name"], "unique_together": {("strain", "location")}},
        ),
    ]
