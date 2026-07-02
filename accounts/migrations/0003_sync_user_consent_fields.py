from django.db import migrations


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def sync_user_consent_fields(apps, schema_editor):
    connection = schema_editor.connection
    tables = set(connection.introspection.table_names())
    if "usuarios" not in tables:
        return

    columns = _column_names(connection, "usuarios")
    missing_columns = {
        "consentimiento_marketing": "boolean NOT NULL DEFAULT FALSE" if connection.vendor != "sqlite" else "bool NOT NULL DEFAULT 0",
        "fecha_consentimiento": "timestamp" if connection.vendor != "sqlite" else "datetime",
    }

    for column_name, sql_type in missing_columns.items():
        if column_name not in columns:
            schema_editor.execute(f"ALTER TABLE usuarios ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_sync_usuarios_schema"),
    ]

    operations = [
        migrations.RunPython(sync_user_consent_fields, migrations.RunPython.noop),
    ]
