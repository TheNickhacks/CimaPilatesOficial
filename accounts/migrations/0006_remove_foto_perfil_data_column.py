from django.db import migrations


def remove_foto_perfil_data_column(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    
    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))
        
    if "usuarios" not in tables:
        return

    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, "usuarios")
        columns = {column.name for column in description}

    if "foto_perfil_data" in columns:
        if vendor == "sqlite":
            try:
                schema_editor.execute("ALTER TABLE usuarios DROP COLUMN foto_perfil_data")
            except Exception:
                # Fallback if SQLite version is older and doesn't support DROP COLUMN
                pass
        else:
            schema_editor.execute("ALTER TABLE usuarios DROP COLUMN foto_perfil_data")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_sync_user_health_fields"),
    ]

    operations = [
        migrations.RunPython(remove_foto_perfil_data_column, migrations.RunPython.noop),
    ]
