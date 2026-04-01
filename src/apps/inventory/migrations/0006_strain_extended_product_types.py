from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0005_strain_card_tone"),
    ]

    operations = [
        migrations.AlterField(
            model_name="strain",
            name="product_type",
            field=models.CharField(
                choices=[
                    ("flower", "Bluete"),
                    ("cutting", "Steckling"),
                    ("edible", "Edible"),
                    ("accessory", "Rauchzubehoer"),
                    ("merch", "Werbegeschenk"),
                ],
                default="flower",
                max_length=16,
            ),
        ),
    ]
