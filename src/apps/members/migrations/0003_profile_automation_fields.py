from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0002_profile_finance_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="last_activity",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="work_hours_done",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=6),
        ),
    ]
