from django.db import migrations


def _table_names(connection):
	with connection.cursor() as cursor:
		return set(connection.introspection.table_names(cursor))


def _column_names(connection, table_name):
	with connection.cursor() as cursor:
		description = connection.introspection.get_table_description(cursor, table_name)
	return {column.name for column in description}


def sync_teacher_hours_adjustments(apps, schema_editor):
	connection = schema_editor.connection
	vendor = connection.vendor
	tables = _table_names(connection)

	if "ajustes_horas_profesoras" not in tables:
		if vendor == "sqlite":
			schema_editor.execute(
				"""
				CREATE TABLE ajustes_horas_profesoras (
					id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
					teacher_id char(32) NOT NULL,
					year integer NOT NULL,
					month integer NOT NULL,
					minutes_delta integer NOT NULL,
					reason text,
					created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
				)
				"""
			)
		else:
			schema_editor.execute(
				"""
				CREATE TABLE ajustes_horas_profesoras (
					id bigserial NOT NULL PRIMARY KEY,
					teacher_id uuid NOT NULL,
					year integer NOT NULL,
					month integer NOT NULL,
					minutes_delta integer NOT NULL,
					reason text,
					created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
				)
				"""
			)

	columns = _column_names(connection, "ajustes_horas_profesoras")
	sql_datetime = "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP"
	missing_columns = {
		"teacher_id": "uuid NOT NULL" if vendor != "sqlite" else "char(32) NOT NULL",
		"year": "integer NOT NULL DEFAULT 0",
		"month": "integer NOT NULL DEFAULT 0",
		"minutes_delta": "integer NOT NULL DEFAULT 0",
		"reason": "text",
		"created_at": sql_datetime,
	}
	for column_name, sql_type in missing_columns.items():
		if column_name not in columns:
			schema_editor.execute(f"ALTER TABLE ajustes_horas_profesoras ADD COLUMN {column_name} {sql_type}")


class Migration(migrations.Migration):
	dependencies = [
		("core", "0009_sync_teacher_monthly_shifts"),
	]

	operations = [
		migrations.RunPython(sync_teacher_hours_adjustments, migrations.RunPython.noop),
	]

