from django.db import migrations


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def sync_user_health_fields(apps, schema_editor):
    connection = schema_editor.connection
    tables = set(connection.introspection.table_names())
    if "usuarios" not in tables:
        return

    columns = _column_names(connection, "usuarios")
    missing_columns = {
        "informacion_salud": "text",
        "consideraciones_clase": "text",
        "contacto_emergencia": "varchar(100)",
        "telefono_emergencia": "varchar(20)",
    }

    for column_name, sql_type in missing_columns.items():
        if column_name not in columns:
            schema_editor.execute(f"ALTER TABLE usuarios ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_sync_user_privacy_fields"),
    ]

    operations = [
        migrations.RunPython(sync_user_health_fields, migrations.RunPython.noop),
    ]
