from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("inventory", "0002_inventory_advanced_features"),
    ]

    operations = [
        migrations.CreateModel(
            name="MotherPlant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("planted_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Aktiv"), ("retired", "Stillgelegt"), ("diseased", "Krank")],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("genetics", models.CharField(blank=True, max_length=255)),
                (
                    "strain",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="mother_plants", to="inventory.strain"),
                ),
            ],
            options={"ordering": ["-planted_date", "id"]},
        ),
        migrations.CreateModel(
            name="Cutting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("planted_date", models.DateField()),
                ("rooting_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("planted", "Gesteckt"), ("rooted", "Bewurzelt"), ("failed", "Fehlgeschlagen")],
                        default="planted",
                        max_length=20,
                    ),
                ),
                (
                    "mother_plant",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cuttings", to="cultivation.motherplant"),
                ),
            ],
            options={"ordering": ["-planted_date", "id"]},
        ),
        migrations.CreateModel(
            name="Plant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("room", models.CharField(max_length=120)),
                ("planting_date", models.DateField()),
                (
                    "growth_stage",
                    models.CharField(
                        choices=[("seedling", "Jungpflanze"), ("vegetative", "Wachstum"), ("flowering", "Bluete"), ("harvested", "Geerntet")],
                        default="seedling",
                        max_length=20,
                    ),
                ),
                (
                    "cutting",
                    models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="plant", to="cultivation.cutting"),
                ),
            ],
            options={"ordering": ["-planting_date", "id"]},
        ),
        migrations.CreateModel(
            name="Harvest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("harvest_date", models.DateField()),
                ("wet_weight", models.DecimalField(decimal_places=2, max_digits=8)),
                ("dry_weight", models.DecimalField(decimal_places=2, max_digits=8)),
                (
                    "plant",
                    models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="harvest", to="cultivation.plant"),
                ),
            ],
            options={"ordering": ["-harvest_date", "-id"]},
        ),
        migrations.CreateModel(
            name="GrowthLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                (
                    "activity_type",
                    models.CharField(
                        choices=[("watering", "Bewaesserung"), ("nutrients", "Duengung"), ("pruning", "Schnitt"), ("health", "Gesundheitscheck")],
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("nutrients", models.CharField(blank=True, max_length=255)),
                (
                    "plant",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="growth_logs", to="cultivation.plant"),
                ),
            ],
            options={"ordering": ["-date", "-id"]},
        ),
        migrations.CreateModel(
            name="BatchConnection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "batch",
                    models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="harvest_connection", to="inventory.batch"),
                ),
                (
                    "harvest",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="batch_connection", to="cultivation.harvest"),
                ),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
