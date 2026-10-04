from django.db import migrations


def add_plan_am(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM planes_catalogo WHERE slug = 'plan-am'")
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                """
                INSERT INTO planes_catalogo (
                    slug, nombre, icono, clases_por_mes, frecuencia, precio_mensual,
                    precio_trimestral, precio_semestral, es_clase_suelta, destacado,
                    descripcion, activo, orden
                ) VALUES (
                    'plan-am', 'Plan AM (Exclusivo AM)', '☀️', 4,
                    '4 clases/mes · Lun a Vie (07:10–12:00)', 28000, 75000, 140000,
                    %s, %s,
                    'Plan matutino de 4 clases mensuales disponible exclusivamente de lunes a viernes en bloque AM (07:10 a 12:00 hrs).',
                    %s, 1
                )
                """,
                [False, True, True],
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0017_add_single_class_attendance_and_indexes"),
    ]

    operations = [
        migrations.RunPython(add_plan_am, migrations.RunPython.noop),
    ]
