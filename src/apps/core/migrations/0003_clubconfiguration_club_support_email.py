from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_clubconfiguration"),
    ]

    operations = [
        migrations.AddField(
            model_name="clubconfiguration",
            name="club_support_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
    ]
