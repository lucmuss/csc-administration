from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0012_profile_probation_until"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="email_verification_code",
            field=models.CharField(blank=True, max_length=12),
        ),
        migrations.AddField(
            model_name="profile",
            name="email_verification_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="email_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="verificationsubmission",
            name="ai_birth_date_match_score",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name="verificationsubmission",
            name="ai_checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="verificationsubmission",
            name="ai_document_type_confidence",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name="verificationsubmission",
            name="ai_is_likely_id_document",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="verificationsubmission",
            name="ai_name_match_score",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name="verificationsubmission",
            name="ai_result_payload",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="verificationsubmission",
            name="ai_result_summary",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="verificationsubmission",
            name="documents_deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
