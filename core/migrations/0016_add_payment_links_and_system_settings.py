from django.db import migrations


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def add_payment_links_and_system_settings(apps, schema_editor):
    connection = schema_editor.connection
    columns = _column_names(connection, "planes_catalogo")

    for col in ("link_pago_mensual", "link_pago_trimestral", "link_pago_semestral", "link_pago_prueba", "link_pago_suelta"):
        if col not in columns:
            schema_editor.execute(f"ALTER TABLE planes_catalogo ADD COLUMN {col} varchar(500)")

    # Ensure configuraciones_sistema table exists
    with connection.cursor() as cursor:
        tables = connection.introspection.table_names(cursor)
        if "configuraciones_sistema" not in tables:
            if connection.vendor == "postgresql":
                schema_editor.execute("""
                    CREATE TABLE configuraciones_sistema (
                        id BIGSERIAL PRIMARY KEY,
                        key VARCHAR(100) NOT NULL UNIQUE,
                        value TEXT,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                schema_editor.execute("""
                    CREATE TABLE configuraciones_sistema (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key VARCHAR(100) NOT NULL UNIQUE,
                        value TEXT,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_add_tipo_clase_to_single_class"),
    ]

    operations = [
        migrations.RunPython(add_payment_links_and_system_settings, migrations.RunPython.noop),
    ]
