from django.db import migrations


def _table_names(connection):
    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor))


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def sync_usuarios_schema(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    tables = _table_names(connection)

    if "usuarios" not in tables:
        if vendor == "sqlite":
            schema_editor.execute(
                """
                CREATE TABLE usuarios (
                    id char(32) NOT NULL PRIMARY KEY,
                    email varchar(100) NOT NULL UNIQUE,
                    password_hash varchar(255) NOT NULL,
                    nombre varchar(100),
                    apellido varchar(100),
                    nombre_completo varchar(100),
                    rut varchar(15) UNIQUE,
                    fecha_nacimiento date,
                    genero varchar(20),
                    telefono varchar(20),
                    rol varchar(20) NOT NULL DEFAULT 'alumna',
                    consentimiento_marketing bool NOT NULL DEFAULT 0,
                    fecha_consentimiento datetime,
                    is_active bool NOT NULL DEFAULT 1,
                    created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    foto_perfil_path varchar(255),
                    foto_perfil_data blob,
                    foto_perfil_mime_type varchar(100)
                )
                """
            )
        else:
            schema_editor.execute(
                """
                CREATE TABLE usuarios (
                    id uuid NOT NULL PRIMARY KEY,
                    email varchar(100) UNIQUE,
                    password_hash varchar(255) NOT NULL,
                    nombre varchar(100),
                    apellido varchar(100),
                    nombre_completo varchar(100),
                    rut varchar(15) UNIQUE,
                    fecha_nacimiento date,
                    genero varchar(20),
                    telefono varchar(20),
                    rol varchar(20) NOT NULL DEFAULT 'alumna',
                    consentimiento_marketing boolean NOT NULL DEFAULT FALSE,
                    fecha_consentimiento timestamp,
                    is_active boolean NOT NULL DEFAULT TRUE,
                    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    foto_perfil_path varchar(255),
                    foto_perfil_data bytea,
                    foto_perfil_mime_type varchar(100)
                )
                """
            )
        return

    columns = _column_names(connection, "usuarios")
    missing_columns = {
        "nombre": "varchar(100)",
        "apellido": "varchar(100)",
        "foto_perfil_path": "varchar(255)",
        "foto_perfil_data": "blob" if vendor == "sqlite" else "bytea",
        "foto_perfil_mime_type": "varchar(100)",
    }

    for column_name, sql_type in missing_columns.items():
        if column_name not in columns:
            schema_editor.execute(f"ALTER TABLE usuarios ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sync_usuarios_schema, migrations.RunPython.noop),
    ]

