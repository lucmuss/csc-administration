from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PublicDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160)),
                ("category", models.CharField(choices=[("statute", "Satzung"), ("policy", "Ordnung / Richtlinie"), ("info", "Information"), ("form", "Formular"), ("other", "Sonstiges")], default="other", max_length=20)),
                ("description", models.TextField(blank=True)),
                ("file", models.FileField(upload_to="documents/")),
                ("is_public", models.BooleanField(default=True)),
                ("display_order", models.PositiveSmallIntegerField(default=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["display_order", "title", "-created_at"]},
        ),
    ]
