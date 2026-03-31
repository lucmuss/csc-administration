from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0005_profile_onboarding_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="account_holder_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="profile",
            name="application_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="instagram_opt_in",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="telegram_opt_in",
            field=models.BooleanField(default=False),
        ),
    ]
