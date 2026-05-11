from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_socialclub_minimum_age"),
    ]

    operations = [
        migrations.AddField(
            model_name="socialclub",
            name="registration_email_verification_code",
            field=models.CharField(blank=True, max_length=12),
        ),
        migrations.AddField(
            model_name="socialclub",
            name="registration_email_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="socialclub",
            name="registration_reminder_7_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="socialclub",
            name="registration_reminder_14_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
