from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("members", "0003_profile_automation_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="Shift",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("required_members", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["starts_at", "id"]},
        ),
        migrations.CreateModel(
            name="WorkHours",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("hours", models.DecimalField(decimal_places=2, max_digits=5)),
                ("notes", models.TextField(blank=True)),
                ("approved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="work_hours", to="members.profile"),
                ),
                (
                    "shift",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="work_hours",
                        to="participation.shift",
                    ),
                ),
            ],
            options={"ordering": ["-date", "-id"]},
        ),
        migrations.CreateModel(
            name="MemberEngagement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("required_hours_year", models.DecimalField(decimal_places=2, default=Decimal("20.00"), max_digits=6)),
                ("annual_meeting_date", models.DateField(blank=True, null=True)),
                ("invitation_sent_at", models.DateTimeField(blank=True, null=True)),
                ("reminder_sent_at", models.DateTimeField(blank=True, null=True)),
                ("registration_deadline", models.DateField(blank=True, null=True)),
                ("registration_completed", models.BooleanField(default=False)),
                ("registration_reminder_sent_at", models.DateTimeField(blank=True, null=True)),
                ("inactivity_notified_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="engagement", to="members.profile"),
                ),
            ],
            options={"ordering": ["profile__member_number", "id"]},
        ),
    ]
