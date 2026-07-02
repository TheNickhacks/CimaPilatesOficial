from django.db import migrations


def _table_names(connection):
    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor))


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def sync_schedule_tables(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    tables = _table_names(connection)

    if "agenda_clases" not in tables:
        if vendor == "sqlite":
            schema_editor.execute(
                """
                CREATE TABLE agenda_clases (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    starts_at datetime NOT NULL UNIQUE,
                    ends_at datetime NOT NULL,
                    capacidad_maxima integer NOT NULL DEFAULT 4,
                    created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            schema_editor.execute(
                """
                CREATE TABLE agenda_clases (
                    id bigserial NOT NULL PRIMARY KEY,
                    starts_at timestamp NOT NULL UNIQUE,
                    ends_at timestamp NOT NULL,
                    capacidad_maxima integer NOT NULL DEFAULT 4,
                    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    if "reservas_clases" not in tables:
        if vendor == "sqlite":
            schema_editor.execute(
                """
                CREATE TABLE reservas_clases (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    class_session_id integer NOT NULL,
                    user_id char(32) NOT NULL,
                    nota text,
                    created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(class_session_id, user_id)
                )
                """
            )
        else:
            schema_editor.execute(
                """
                CREATE TABLE reservas_clases (
                    id bigserial NOT NULL PRIMARY KEY,
                    class_session_id bigint NOT NULL,
                    user_id uuid NOT NULL,
                    nota text,
                    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(class_session_id, user_id)
                )
                """
            )

    if "agenda_clases" in _table_names(connection):
        columns = _column_names(connection, "agenda_clases")
        missing_columns = {
            "starts_at": "timestamp NOT NULL" if vendor != "sqlite" else "datetime NOT NULL",
            "ends_at": "timestamp NOT NULL" if vendor != "sqlite" else "datetime NOT NULL",
            "capacidad_maxima": "integer NOT NULL DEFAULT 4",
            "created_at": "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column_name, sql_type in missing_columns.items():
            if column_name not in columns:
                schema_editor.execute(f"ALTER TABLE agenda_clases ADD COLUMN {column_name} {sql_type}")

    if "reservas_clases" in _table_names(connection):
        columns = _column_names(connection, "reservas_clases")
        missing_columns = {
            "class_session_id": "bigint" if vendor != "sqlite" else "integer",
            "user_id": "uuid" if vendor != "sqlite" else "char(32)",
            "nota": "text",
            "created_at": "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column_name, sql_type in missing_columns.items():
            if column_name not in columns:
                schema_editor.execute(f"ALTER TABLE reservas_clases ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_sync_plan_catalog_and_requests"),
    ]

    operations = [
        migrations.RunPython(sync_schedule_tables, migrations.RunPython.noop),
    ]
