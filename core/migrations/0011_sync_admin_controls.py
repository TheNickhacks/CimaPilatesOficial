from django.db import migrations


def _table_names(connection):
    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor))


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def sync_admin_controls_tables(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    tables = _table_names(connection)

    if "agenda_clases" in tables:
        columns = _column_names(connection, "agenda_clases")
        missing_columns = {
            "is_blocked": "boolean NOT NULL DEFAULT FALSE" if vendor != "sqlite" else "bool NOT NULL DEFAULT 0",
            "blocked_reason": "text",
        }
        for column_name, sql_type in missing_columns.items():
            if column_name not in columns:
                schema_editor.execute(f"ALTER TABLE agenda_clases ADD COLUMN {column_name} {sql_type}")

    if "registro_admin_acciones" not in tables:
        if vendor == "sqlite":
            schema_editor.execute(
                """
                CREATE TABLE registro_admin_acciones (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    actor_id char(32),
                    action_type varchar(50) NOT NULL,
                    target_user_id char(32),
                    plan_request_id integer,
                    class_session_id integer,
                    details text,
                    created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            schema_editor.execute(
                """
                CREATE TABLE registro_admin_acciones (
                    id bigserial NOT NULL PRIMARY KEY,
                    actor_id uuid,
                    action_type varchar(50) NOT NULL,
                    target_user_id uuid,
                    plan_request_id bigint,
                    class_session_id bigint,
                    details text,
                    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    if "registro_admin_acciones" in _table_names(connection):
        columns = _column_names(connection, "registro_admin_acciones")
        missing_columns = {
            "actor_id": "uuid" if vendor != "sqlite" else "char(32)",
            "action_type": "varchar(50) NOT NULL DEFAULT ''",
            "target_user_id": "uuid" if vendor != "sqlite" else "char(32)",
            "plan_request_id": "bigint" if vendor != "sqlite" else "integer",
            "class_session_id": "bigint" if vendor != "sqlite" else "integer",
            "details": "text",
            "created_at": "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column_name, sql_type in missing_columns.items():
            if column_name not in columns:
                schema_editor.execute(f"ALTER TABLE registro_admin_acciones ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_sync_teacher_hours_adjustments"),
    ]

    operations = [
        migrations.RunPython(sync_admin_controls_tables, migrations.RunPython.noop),
    ]
