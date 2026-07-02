from django.db import migrations


def _table_names(connection):
    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor))


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def sync_landing_leads_schema(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    tables = _table_names(connection)

    if "landing_leads" not in tables:
        if vendor == "sqlite":
            schema_editor.execute(
                """
                CREATE TABLE landing_leads (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    nombre varchar(100) NOT NULL,
                    rut varchar(15),
                    email varchar(100) NOT NULL,
                    telefono varchar(20) NOT NULL,
                    registered_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            schema_editor.execute(
                """
                CREATE TABLE landing_leads (
                    id bigserial NOT NULL PRIMARY KEY,
                    nombre varchar(100) NOT NULL,
                    rut varchar(15),
                    email varchar(100) NOT NULL,
                    telefono varchar(20) NOT NULL,
                    registered_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        return

    columns = _column_names(connection, "landing_leads")
    if "rut" not in columns:
        schema_editor.execute("ALTER TABLE landing_leads ADD COLUMN rut varchar(15)")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sync_landing_leads_schema, migrations.RunPython.noop),
    ]

