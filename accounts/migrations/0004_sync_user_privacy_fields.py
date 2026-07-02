from django.db import migrations


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def sync_user_privacy_fields(apps, schema_editor):
    connection = schema_editor.connection
    tables = set(connection.introspection.table_names())
    if "usuarios" not in tables:
        return

    columns = _column_names(connection, "usuarios")
    missing_columns = {
        "solicitud_eliminacion_datos": "boolean NOT NULL DEFAULT FALSE" if connection.vendor != "sqlite" else "bool NOT NULL DEFAULT 0",
        "fecha_solicitud_eliminacion": "timestamp" if connection.vendor != "sqlite" else "datetime",
    }

    for column_name, sql_type in missing_columns.items():
        if column_name not in columns:
            schema_editor.execute(f"ALTER TABLE usuarios ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_sync_user_consent_fields"),
    ]

    operations = [
        migrations.RunPython(sync_user_privacy_fields, migrations.RunPython.noop),
    ]
