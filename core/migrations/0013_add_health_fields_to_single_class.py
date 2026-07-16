from django.db import migrations


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def add_health_fields_to_single_class(apps, schema_editor):
    connection = schema_editor.connection
    columns = _column_names(connection, "solicitudes_clase_suelta")

    missing_columns = {
        "edad": "integer",
        "operaciones_lesiones": "text",
        "condiciones_medicas": "text",
    }

    for column_name, sql_type in missing_columns.items():
        if column_name not in columns:
            schema_editor.execute(f"ALTER TABLE solicitudes_clase_suelta ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_full_state_sync"),
    ]

    operations = [
        migrations.RunPython(add_health_fields_to_single_class, migrations.RunPython.noop),
    ]
