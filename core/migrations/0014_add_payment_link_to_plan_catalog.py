from django.db import migrations


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def add_payment_link_to_plan_catalog(apps, schema_editor):
    connection = schema_editor.connection
    columns = _column_names(connection, "planes_catalogo")

    if "link_pago" not in columns:
        schema_editor.execute("ALTER TABLE planes_catalogo ADD COLUMN link_pago varchar(500)")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_add_health_fields_to_single_class"),
    ]

    operations = [
        migrations.RunPython(add_payment_link_to_plan_catalog, migrations.RunPython.noop),
    ]
