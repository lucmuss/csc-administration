from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Strain",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("thc", models.DecimalField(decimal_places=2, max_digits=5)),
                ("cbd", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=5)),
                ("price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("stock", models.DecimalField(decimal_places=2, max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
    ]
