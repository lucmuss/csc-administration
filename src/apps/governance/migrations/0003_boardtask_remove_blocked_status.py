from django.db import migrations, models


def migrate_blocked_to_in_progress(apps, schema_editor):
    BoardTask = apps.get_model("governance", "BoardTask")
    BoardTask.objects.filter(status="blocked").update(status="in_progress")


class Migration(migrations.Migration):
    dependencies = [
        ("governance", "0002_boardmeeting_notifications"),
    ]

    operations = [
        migrations.RunPython(migrate_blocked_to_in_progress, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="boardtask",
            name="status",
            field=models.CharField(
                choices=[("todo", "Offen"), ("in_progress", "In Arbeit"), ("done", "Erledigt")],
                default="todo",
                max_length=20,
            ),
        ),
    ]
