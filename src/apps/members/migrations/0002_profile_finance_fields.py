from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0001_initial"),
        ("members", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="is_locked_for_orders",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="sepa_mandate",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="active_for_profile",
                to="finance.sepamandate",
            ),
        ),
    ]
