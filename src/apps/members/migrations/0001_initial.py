import datetime
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("birth_date", models.DateField()),
                ("member_number", models.BigIntegerField(blank=True, null=True, unique=True)),
                ("status", models.CharField(choices=[("pending", "Ausstehend"), ("verified", "Verifiziert"), ("active", "Aktiv"), ("rejected", "Abgelehnt")], default="pending", max_length=16)),
                ("is_verified", models.BooleanField(default=False)),
                ("balance", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("daily_used", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=6)),
                ("monthly_used", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=6)),
                ("daily_counter_date", models.DateField(default=datetime.date.today)),
                ("monthly_counter_key", models.CharField(default="1970-01", max_length=7)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["member_number", "id"]},
        ),
    ]
