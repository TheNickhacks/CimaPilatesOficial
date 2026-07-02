from django.db import migrations


def _table_names(connection):
	with connection.cursor() as cursor:
		return set(connection.introspection.table_names(cursor))


def _column_names(connection, table_name):
	with connection.cursor() as cursor:
		description = connection.introspection.get_table_description(cursor, table_name)
	return {column.name for column in description}


def sync_class_credit_adjustments_table(apps, schema_editor):
	connection = schema_editor.connection
	vendor = connection.vendor
	tables = _table_names(connection)

	if "ajustes_clases" not in tables:
		if vendor == "sqlite":
			schema_editor.execute(
				"""
				CREATE TABLE ajustes_clases (
					id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
					user_id char(32) NOT NULL,
					plan_request_id integer,
					cantidad integer NOT NULL,
					motivo text,
					created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
				)
				"""
			)
		else:
			schema_editor.execute(
				"""
				CREATE TABLE ajustes_clases (
					id bigserial NOT NULL PRIMARY KEY,
					user_id uuid NOT NULL,
					plan_request_id bigint,
					cantidad integer NOT NULL,
					motivo text,
					created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
				)
				"""
			)

	columns = _column_names(connection, "ajustes_clases")
	sql_datetime = "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP"
	missing_columns = {
		"user_id": "uuid NOT NULL" if vendor != "sqlite" else "char(32) NOT NULL",
		"plan_request_id": "bigint" if vendor != "sqlite" else "integer",
		"cantidad": "integer NOT NULL DEFAULT 0",
		"motivo": "text",
		"created_at": sql_datetime,
	}
	for column_name, sql_type in missing_columns.items():
		if column_name not in columns:
			schema_editor.execute(f"ALTER TABLE ajustes_clases ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
	dependencies = [
		("core", "0006_sync_reservation_confirmation"),
	]

	operations = [
		migrations.RunPython(sync_class_credit_adjustments_table, migrations.RunPython.noop),
	]

