from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0002_inventory_advanced_features"),
    ]

    operations = [
        migrations.AddField(
            model_name="strain",
            name="image",
            field=models.FileField(blank=True, upload_to="strains/"),
        ),
    ]
