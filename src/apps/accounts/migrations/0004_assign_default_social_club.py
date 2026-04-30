from django.db import migrations
import os


def assign_default_social_club(apps, schema_editor):
    SocialClub = apps.get_model("core", "SocialClub")
    User = apps.get_model("accounts", "User")
    default_club_name = os.getenv("CSC_DEFAULT_SOCIAL_CLUB_NAME", "Cannabis Social Club Leipzig Sued")
    default_club, _ = SocialClub.objects.get_or_create(
        name=default_club_name,
        defaults={
            "email": "info@csc-leipzig-sued.de",
            "street_address": "Mannheimer Strasse 132",
            "postal_code": "04209",
            "city": "Leipzig",
            "phone": "+493412000000",
            "website": "https://csc.kolibri-kollektiv.eu",
            "is_active": True,
            "is_approved": True,
        },
    )
    User.objects.filter(social_club__isnull=True).update(social_club=default_club)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_socialclub"),
        ("accounts", "0003_user_social_club"),
    ]

    operations = [
        migrations.RunPython(assign_default_social_club, noop_reverse),
    ]
