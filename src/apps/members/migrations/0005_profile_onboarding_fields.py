from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0004_profile_members_pro_status_4af664_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="bank_name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="profile",
            name="city",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="profile",
            name="desired_join_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="direct_debit_accepted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="german_residence_confirmed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="id_document_confirmed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="important_newsletter_opt_in",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="minimum_age_confirmed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="no_other_csc_membership",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="optional_newsletter_opt_in",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="phone",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="profile",
            name="postal_code",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name="profile",
            name="privacy_accepted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="registration_completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="street_address",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
