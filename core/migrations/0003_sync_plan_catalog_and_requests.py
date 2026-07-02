from django.db import migrations


PLAN_ROWS = [
    ("plan-4", "4 clases al mes", "04", 4, "1 vez por semana", 35990, 96990, 188990, False, False, "Plan ideal para comenzar con constancia.", True, 1),
    ("plan-8", "8 clases al mes", "08", 8, "2 veces por semana", 56990, 153990, 298990, False, True, "El plan mas elegido para progreso sostenido.", True, 2),
    ("plan-12", "12 clases al mes", "12", 12, "3 veces por semana", 79990, 215990, 419990, False, False, "Mayor frecuencia para potenciar resultados.", True, 3),
    ("plan-16", "16 clases al mes", "16", 16, "4 veces por semana", 85990, 232990, 450990, False, False, "Formato intensivo para entrenamiento continuo.", True, 4),
    ("clase-suelta", "Clase suelta", "01", 1, "Asistencia flexible", 9990, 9990, 9990, True, False, "Perfecta para conocer el estudio o asistir de forma puntual.", True, 5),
]


def _table_names(connection):
    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor))


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def sync_plan_tables(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    tables = _table_names(connection)

    if "planes_catalogo" not in tables:
        if vendor == "sqlite":
            schema_editor.execute(
                """
                CREATE TABLE planes_catalogo (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    slug varchar(50) NOT NULL UNIQUE,
                    nombre varchar(100) NOT NULL,
                    icono varchar(10) NOT NULL,
                    clases_por_mes integer NOT NULL,
                    frecuencia varchar(60) NOT NULL,
                    precio_mensual integer NOT NULL,
                    precio_trimestral integer NOT NULL,
                    precio_semestral integer NOT NULL,
                    es_clase_suelta bool NOT NULL DEFAULT 0,
                    destacado bool NOT NULL DEFAULT 0,
                    descripcion varchar(255),
                    activo bool NOT NULL DEFAULT 1,
                    orden integer NOT NULL DEFAULT 0,
                    created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            schema_editor.execute(
                """
                CREATE TABLE planes_catalogo (
                    id bigserial NOT NULL PRIMARY KEY,
                    slug varchar(50) NOT NULL UNIQUE,
                    nombre varchar(100) NOT NULL,
                    icono varchar(10) NOT NULL,
                    clases_por_mes integer NOT NULL,
                    frecuencia varchar(60) NOT NULL,
                    precio_mensual integer NOT NULL,
                    precio_trimestral integer NOT NULL,
                    precio_semestral integer NOT NULL,
                    es_clase_suelta boolean NOT NULL DEFAULT FALSE,
                    destacado boolean NOT NULL DEFAULT FALSE,
                    descripcion varchar(255),
                    activo boolean NOT NULL DEFAULT TRUE,
                    orden integer NOT NULL DEFAULT 0,
                    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    if "solicitudes_planes" not in tables:
        if vendor == "sqlite":
            schema_editor.execute(
                """
                CREATE TABLE solicitudes_planes (
                    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    user_id char(32) NOT NULL,
                    plan_id integer NOT NULL,
                    periodo varchar(20) NOT NULL,
                    metodo_pago varchar(20) NOT NULL DEFAULT 'presencial',
                    detalle_transferencia text,
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
                CREATE TABLE solicitudes_planes (
                    id bigserial NOT NULL PRIMARY KEY,
                    user_id uuid NOT NULL,
                    plan_id bigint NOT NULL,
                    periodo varchar(20) NOT NULL,
                    metodo_pago varchar(20) NOT NULL DEFAULT 'presencial',
                    detalle_transferencia text,
                    notas text,
                    comprobante_path varchar(255),
                    estado varchar(20) NOT NULL DEFAULT 'pendiente',
                    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    if "planes_catalogo" in _table_names(connection):
        columns = _column_names(connection, "planes_catalogo")
        missing_plan_columns = {
            "icono": "varchar(10)",
            "clases_por_mes": "integer NOT NULL DEFAULT 0",
            "frecuencia": "varchar(60) NOT NULL DEFAULT ''",
            "precio_mensual": "integer NOT NULL DEFAULT 0",
            "precio_trimestral": "integer NOT NULL DEFAULT 0",
            "precio_semestral": "integer NOT NULL DEFAULT 0",
            "es_clase_suelta": "boolean NOT NULL DEFAULT FALSE" if vendor != "sqlite" else "bool NOT NULL DEFAULT 0",
            "destacado": "boolean NOT NULL DEFAULT FALSE" if vendor != "sqlite" else "bool NOT NULL DEFAULT 0",
            "descripcion": "varchar(255)",
            "activo": "boolean NOT NULL DEFAULT TRUE" if vendor != "sqlite" else "bool NOT NULL DEFAULT 1",
            "orden": "integer NOT NULL DEFAULT 0",
            "created_at": "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column_name, sql_type in missing_plan_columns.items():
            if column_name not in columns:
                schema_editor.execute(f"ALTER TABLE planes_catalogo ADD COLUMN {column_name} {sql_type}")

    if "solicitudes_planes" in _table_names(connection):
        columns = _column_names(connection, "solicitudes_planes")
        missing_request_columns = {
            "user_id": "uuid" if vendor != "sqlite" else "char(32)",
            "plan_id": "bigint" if vendor != "sqlite" else "integer",
            "periodo": "varchar(20) NOT NULL DEFAULT 'monthly'",
            "metodo_pago": "varchar(20) NOT NULL DEFAULT 'presencial'",
            "detalle_transferencia": "text",
            "notas": "text",
            "comprobante_path": "varchar(255)",
            "estado": "varchar(20) NOT NULL DEFAULT 'pendiente'",
            "created_at": "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
        }
        for column_name, sql_type in missing_request_columns.items():
            if column_name not in columns:
                schema_editor.execute(f"ALTER TABLE solicitudes_planes ADD COLUMN {column_name} {sql_type}")

    with connection.cursor() as cursor:
        for row in PLAN_ROWS:
            cursor.execute(
                """
                INSERT INTO planes_catalogo (
                    slug, nombre, icono, clases_por_mes, frecuencia, precio_mensual,
                    precio_trimestral, precio_semestral, es_clase_suelta, destacado,
                    descripcion, activo, orden
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(slug) DO UPDATE SET
                    nombre = excluded.nombre,
                    icono = excluded.icono,
                    clases_por_mes = excluded.clases_por_mes,
                    frecuencia = excluded.frecuencia,
                    precio_mensual = excluded.precio_mensual,
                    precio_trimestral = excluded.precio_trimestral,
                    precio_semestral = excluded.precio_semestral,
                    es_clase_suelta = excluded.es_clase_suelta,
                    destacado = excluded.destacado,
                    descripcion = excluded.descripcion,
                    activo = excluded.activo,
                    orden = excluded.orden,
                    updated_at = CURRENT_TIMESTAMP
                """,
                row,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_sync_landing_leads_schema"),
    ]

    operations = [
        migrations.RunPython(sync_plan_tables, migrations.RunPython.noop),
    ]
