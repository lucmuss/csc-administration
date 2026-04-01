from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0004_alter_uploadedinvoice_amount_gross_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="uploadedinvoice",
            name="title",
            field=models.CharField(blank=True, max_length=180),
        ),
    ]
