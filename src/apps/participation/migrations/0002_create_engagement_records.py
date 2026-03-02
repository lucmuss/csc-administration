from django.db import migrations


def create_engagements(apps, schema_editor):
    Profile = apps.get_model("members", "Profile")
    MemberEngagement = apps.get_model("participation", "MemberEngagement")

    for profile in Profile.objects.all():
        MemberEngagement.objects.get_or_create(profile=profile)


class Migration(migrations.Migration):
    dependencies = [
        ("participation", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_engagements, migrations.RunPython.noop),
    ]
