from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("governance", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="boardmeeting",
            name="agenda_submission_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="boardmeeting",
            name="invitation_lead_days",
            field=models.PositiveSmallIntegerField(default=14),
        ),
        migrations.AddField(
            model_name="boardmeeting",
            name="minutes_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="boardmeeting",
            name="participation_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="boardmeeting",
            name="reminder_lead_hours",
            field=models.PositiveSmallIntegerField(default=24),
        ),
        migrations.AddField(
            model_name="boardmeeting",
            name="reminder_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
