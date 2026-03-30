from django.db import migrations, models


def infer_product_types(apps, schema_editor):
    Strain = apps.get_model("inventory", "Strain")
    for strain in Strain.objects.all():
        if strain.name.startswith("Steckling:"):
            strain.product_type = "cutting"
        else:
            strain.product_type = "flower"
        strain.save(update_fields=["product_type"])


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0003_strain_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="strain",
            name="product_type",
            field=models.CharField(
                choices=[("flower", "Bluete"), ("cutting", "Steckling"), ("edible", "Edible")],
                default="flower",
                max_length=16,
            ),
        ),
        migrations.RunPython(infer_product_types, migrations.RunPython.noop),
    ]
