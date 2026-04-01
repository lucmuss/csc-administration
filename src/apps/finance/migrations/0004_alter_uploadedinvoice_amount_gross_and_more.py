from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0003_uploadedinvoice"),
    ]

    operations = [
        migrations.AlterField(
            model_name="uploadedinvoice",
            name="amount_gross",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10),
        ),
        migrations.AlterField(
            model_name="uploadedinvoice",
            name="amount_net",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10),
        ),
        migrations.AlterField(
            model_name="uploadedinvoice",
            name="amount_tax",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10),
        ),
    ]
