from django.db import migrations


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def add_single_class_attendance_and_indexes(apps, schema_editor):
    connection = schema_editor.connection
    columns = _column_names(connection, "solicitudes_clase_suelta")

    if "asistio" not in columns:
        if connection.vendor == "postgresql":
            schema_editor.execute("ALTER TABLE solicitudes_clase_suelta ADD COLUMN asistio boolean DEFAULT false")
        else:
            schema_editor.execute("ALTER TABLE solicitudes_clase_suelta ADD COLUMN asistio boolean DEFAULT 0")

    # Non-destructive indexes for performance
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_solicitudes_clase_suelta_session_estado ON solicitudes_clase_suelta(class_session_id, estado);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_solicitudes_planes_user_estado ON solicitudes_planes(user_id, estado);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservas_clases_user ON reservas_clases(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asistencias_clases_session_user ON asistencias_clases(class_session_id, user_id);")
        else:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_solicitudes_clase_suelta_session_estado ON solicitudes_clase_suelta(class_session_id, estado);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_solicitudes_planes_user_estado ON solicitudes_planes(user_id, estado);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservas_clases_user ON reservas_clases(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asistencias_clases_session_user ON asistencias_clases(class_session_id, user_id);")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_add_payment_links_and_system_settings"),
    ]

    operations = [
        migrations.RunPython(add_single_class_attendance_and_indexes, migrations.RunPython.noop),
    ]
