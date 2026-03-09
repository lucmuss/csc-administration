from django.db import migrations

LEGACY_SUFFIX = "_legacy_pre_uuid"


def _column_type(connection, table_name, column_name):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = %s
              AND column_name = %s
            """,
            [table_name, column_name],
        )
        row = cursor.fetchone()
    return row[0] if row else None


def _rename_legacy_table(schema_editor, existing_tables, table_name):
    legacy_name = f"{table_name}{LEGACY_SUFFIX}"
    if table_name not in existing_tables or legacy_name in existing_tables:
        return

    quote = schema_editor.quote_name
    schema_editor.execute(f"ALTER TABLE {quote(table_name)} RENAME TO {quote(legacy_name)}")
    existing_tables.remove(table_name)
    existing_tables.add(legacy_name)


def ensure_cultivation_schema(apps, schema_editor):
    connection = schema_editor.connection
    existing_tables = set(connection.introspection.table_names())

    if "cultivation_plant" in existing_tables and _column_type(connection, "cultivation_plant", "id") != "uuid":
        _rename_legacy_table(schema_editor, existing_tables, "cultivation_plant")

    if (
        "cultivation_harvestbatch_plants" in existing_tables
        and _column_type(connection, "cultivation_harvestbatch_plants", "plant_id") != "uuid"
    ):
        _rename_legacy_table(schema_editor, existing_tables, "cultivation_harvestbatch_plants")

    model_names = [
        "GrowCycle",
        "Plant",
        "HarvestBatch",
        "PlantLog",
    ]

    for model_name in model_names:
        model = apps.get_model("cultivation", model_name)
        if model._meta.db_table not in existing_tables:
            schema_editor.create_model(model)
            existing_tables.add(model._meta.db_table)


class Migration(migrations.Migration):
    dependencies = [
        ("cultivation", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(ensure_cultivation_schema, migrations.RunPython.noop),
    ]
