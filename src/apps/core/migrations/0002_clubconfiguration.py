from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClubConfiguration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("app_name", models.CharField(blank=True, max_length=120)),
                ("app_tagline", models.CharField(blank=True, max_length=160)),
                ("app_description", models.TextField(blank=True)),
                ("club_name", models.CharField(blank=True, max_length=180)),
                ("club_slogan", models.CharField(blank=True, max_length=180)),
                ("club_contact_email", models.EmailField(blank=True, max_length=254)),
                ("club_contact_phone", models.CharField(blank=True, max_length=80)),
                ("club_contact_address", models.TextField(blank=True)),
                ("club_board_representatives", models.TextField(blank=True)),
                ("club_register_entry", models.CharField(blank=True, max_length=180)),
                ("club_register_court", models.CharField(blank=True, max_length=180)),
                ("club_tax_number", models.CharField(blank=True, max_length=180)),
                ("club_vat_id", models.CharField(blank=True, max_length=180)),
                ("club_supervisory_authority", models.CharField(blank=True, max_length=180)),
                ("club_content_responsible", models.CharField(blank=True, max_length=180)),
                ("club_responsible_person", models.TextField(blank=True)),
                ("club_membership_email", models.EmailField(blank=True, max_length=254)),
                ("club_prevention_email", models.EmailField(blank=True, max_length=254)),
                ("club_finance_email", models.EmailField(blank=True, max_length=254)),
                ("club_privacy_contact", models.EmailField(blank=True, max_length=254)),
                ("club_data_protection_officer", models.CharField(blank=True, max_length=180)),
                ("club_language_notice", models.TextField(blank=True)),
                ("club_legal_basis_notice", models.TextField(blank=True)),
                ("club_retention_notice", models.TextField(blank=True)),
                ("club_external_services_text", models.TextField(blank=True)),
                ("prevention_officer_name", models.CharField(blank=True, max_length=180)),
                ("prevention_notice", models.TextField(blank=True)),
                ("instagram_url", models.URLField(blank=True)),
                ("email_signature_text", models.TextField(blank=True)),
                ("email_signature_html", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Club-Konfiguration",
                "verbose_name_plural": "Club-Konfiguration",
            },
        ),
    ]
