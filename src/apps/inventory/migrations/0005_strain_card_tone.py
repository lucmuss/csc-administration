from django.db import migrations, models


def assign_default_card_tones(apps, schema_editor):
    Strain = apps.get_model("inventory", "Strain")
    for strain in Strain.objects.all():
        if strain.product_type == "cutting":
            strain.card_tone = "mint"
        elif strain.product_type == "edible":
            strain.card_tone = "sky"
        else:
            strain.card_tone = "apricot"
        strain.save(update_fields=["card_tone"])


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0004_strain_product_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="strain",
            name="card_tone",
            field=models.CharField(
                choices=[
                    ("apricot", "Apricot"),
                    ("mint", "Mint"),
                    ("sky", "Sky"),
                    ("lilac", "Lilac"),
                    ("sand", "Sand"),
                    ("blush", "Blush"),
                ],
                default="apricot",
                max_length=16,
            ),
        ),
        migrations.RunPython(assign_default_card_tones, migrations.RunPython.noop),
    ]
