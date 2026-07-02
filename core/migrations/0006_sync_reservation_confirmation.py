from django.db import migrations


def _table_names(connection):
	with connection.cursor() as cursor:
		return set(connection.introspection.table_names(cursor))


def _column_names(connection, table_name):
	with connection.cursor() as cursor:
		description = connection.introspection.get_table_description(cursor, table_name)
	return {column.name for column in description}


def sync_reservation_confirmation_columns(apps, schema_editor):
	connection = schema_editor.connection
	vendor = connection.vendor

	if "reservas_clases" not in _table_names(connection):
		return

	columns = _column_names(connection, "reservas_clases")
	sql_datetime = "timestamp" if vendor != "sqlite" else "datetime"
	missing_columns = {
		"confirmation_requested_at": f"{sql_datetime}",
		"confirmed_at": f"{sql_datetime}",
	}
	for column_name, sql_type in missing_columns.items():
		if column_name not in columns:
			schema_editor.execute(f"ALTER TABLE reservas_clases ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
	dependencies = [
		("core", "0005_sync_single_class_requests"),
	]

	operations = [
		migrations.RunPython(sync_reservation_confirmation_columns, migrations.RunPython.noop),
	]

