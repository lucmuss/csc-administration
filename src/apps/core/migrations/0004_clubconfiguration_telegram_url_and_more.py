from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_clubconfiguration_club_support_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="clubconfiguration",
            name="telegram_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="clubconfiguration",
            name="whatsapp_url",
            field=models.URLField(blank=True),
        ),
    ]
