from django.db import migrations


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def add_tipo_clase_to_single_class(apps, schema_editor):
    connection = schema_editor.connection
    columns = _column_names(connection, "solicitudes_clase_suelta")

    if "tipo_clase" not in columns:
        schema_editor.execute("ALTER TABLE solicitudes_clase_suelta ADD COLUMN tipo_clase varchar(30) DEFAULT 'prueba'")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_add_payment_link_to_plan_catalog"),
    ]

    operations = [
        migrations.RunPython(add_tipo_clase_to_single_class, migrations.RunPython.noop),
    ]
