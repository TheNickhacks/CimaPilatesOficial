from django.db import migrations


def remove_remaining_profile_photo_fields(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    
    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))
        
    if "usuarios" not in tables:
        return

    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, "usuarios")
        columns = {column.name for column in description}

    for col in ["foto_perfil_path", "foto_perfil_mime_type"]:
        if col in columns:
            if vendor == "sqlite":
                try:
                    schema_editor.execute(f"ALTER TABLE usuarios DROP COLUMN {col}")
                except Exception:
                    pass
            else:
                schema_editor.execute(f"ALTER TABLE usuarios DROP COLUMN {col}")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_remove_foto_perfil_data_column"),
    ]

    operations = [
        migrations.RunPython(remove_remaining_profile_photo_fields, migrations.RunPython.noop),
    ]
