from django.db import migrations


def _table_names(connection):
    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor))


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def sync_single_class_requests(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    tables = _table_names(connection)

    if "solicitudes_clase_suelta" not in tables:
        if vendor == "sqlite":
            schema_editor.execute(
                """
                CREATE TABLE solicitudes_clase_suelta (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    class_session_id integer NOT NULL,
                    nombre varchar(100) NOT NULL,
                    apellido varchar(100),
                    rut varchar(15) NOT NULL,
                    email varchar(100) NOT NULL,
                    telefono varchar(20) NOT NULL,
                    metodo_pago varchar(20) NOT NULL DEFAULT 'presencial',
                    notas text,
                    comprobante_path varchar(255),
                    estado varchar(20) NOT NULL DEFAULT 'pendiente',
                    created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            schema_editor.execute(
                """
                CREATE TABLE solicitudes_clase_suelta (
                    id bigserial NOT NULL PRIMARY KEY,
                    class_session_id bigint NOT NULL,
                    nombre varchar(100) NOT NULL,
                    apellido varchar(100),
                    rut varchar(15) NOT NULL,
                    email varchar(100) NOT NULL,
                    telefono varchar(20) NOT NULL,
                    metodo_pago varchar(20) NOT NULL DEFAULT 'presencial',
                    notas text,
                    comprobante_path varchar(255),
                    estado varchar(20) NOT NULL DEFAULT 'pendiente',
                    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    columns = _column_names(connection, "solicitudes_clase_suelta")
    missing_columns = {
        "class_session_id": "bigint" if vendor != "sqlite" else "integer",
        "nombre": "varchar(100) NOT NULL DEFAULT ''",
        "apellido": "varchar(100)",
        "rut": "varchar(15) NOT NULL DEFAULT ''",
        "email": "varchar(100) NOT NULL DEFAULT ''",
        "telefono": "varchar(20) NOT NULL DEFAULT ''",
        "metodo_pago": "varchar(20) NOT NULL DEFAULT 'presencial'",
        "notas": "text",
        "comprobante_path": "varchar(255)",
        "estado": "varchar(20) NOT NULL DEFAULT 'pendiente'",
        "created_at": "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
    }
    for column_name, sql_type in missing_columns.items():
        if column_name not in columns:
            schema_editor.execute(f"ALTER TABLE solicitudes_clase_suelta ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_sync_schedule_tables"),
    ]

    operations = [
        migrations.RunPython(sync_single_class_requests, migrations.RunPython.noop),
    ]
