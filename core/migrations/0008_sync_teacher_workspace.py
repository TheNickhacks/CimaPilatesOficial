from django.db import migrations


def _table_names(connection):
	with connection.cursor() as cursor:
		return set(connection.introspection.table_names(cursor))


def _column_names(connection, table_name):
	with connection.cursor() as cursor:
		description = connection.introspection.get_table_description(cursor, table_name)
	return {column.name for column in description}


def _ensure_table(schema_editor, connection, table_name, sqlite_sql, postgres_sql):
	if table_name in _table_names(connection):
		return
	if connection.vendor == "sqlite":
		schema_editor.execute(sqlite_sql)
	else:
		schema_editor.execute(postgres_sql)


def _ensure_columns(schema_editor, connection, table_name, missing_columns):
	columns = _column_names(connection, table_name)
	for column_name, sql_type in missing_columns.items():
		if column_name not in columns:
			schema_editor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}")


def sync_teacher_workspace(apps, schema_editor):
	connection = schema_editor.connection
	vendor = connection.vendor
	timestamp_sql = "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP" if vendor != "sqlite" else "datetime NOT NULL DEFAULT CURRENT_TIMESTAMP"
	date_sql = "date NOT NULL"
	user_fk_sql = "uuid NOT NULL" if vendor != "sqlite" else "char(32) NOT NULL"
	session_fk_sql = "bigint NOT NULL" if vendor != "sqlite" else "integer NOT NULL"
	optional_user_fk_sql = "uuid" if vendor != "sqlite" else "char(32)"
	optional_plan_fk_sql = "bigint" if vendor != "sqlite" else "integer"

	_ensure_table(
		schema_editor,
		connection,
		"turnos_profesoras",
		"""
		CREATE TABLE turnos_profesoras (
			id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
			teacher_id char(32) NOT NULL,
			shift_date date NOT NULL,
			shift_kind varchar(20) NOT NULL,
			created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
		)
		""",
		"""
		CREATE TABLE turnos_profesoras (
			id bigserial NOT NULL PRIMARY KEY,
			teacher_id uuid NOT NULL,
			shift_date date NOT NULL,
			shift_kind varchar(20) NOT NULL,
			created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
		)
		""",
	)
	_ensure_columns(
		schema_editor,
		connection,
		"turnos_profesoras",
		{
			"teacher_id": user_fk_sql,
			"shift_date": date_sql,
			"shift_kind": "varchar(20) NOT NULL DEFAULT 'am'",
			"created_at": timestamp_sql,
		},
	)

	_ensure_table(
		schema_editor,
		connection,
		"asistencias_clases",
		"""
		CREATE TABLE asistencias_clases (
			id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
			class_session_id integer NOT NULL,
			user_id char(32) NOT NULL,
			teacher_id char(32),
			present bool NOT NULL DEFAULT 0,
			marked_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
			created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
		)
		""",
		"""
		CREATE TABLE asistencias_clases (
			id bigserial NOT NULL PRIMARY KEY,
			class_session_id bigint NOT NULL,
			user_id uuid NOT NULL,
			teacher_id uuid,
			present boolean NOT NULL DEFAULT false,
			marked_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
			created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
		)
		""",
	)
	_ensure_columns(
		schema_editor,
		connection,
		"asistencias_clases",
		{
			"class_session_id": session_fk_sql,
			"user_id": user_fk_sql,
			"teacher_id": optional_user_fk_sql,
			"present": "boolean NOT NULL DEFAULT false" if vendor != "sqlite" else "bool NOT NULL DEFAULT 0",
			"marked_at": timestamp_sql,
			"created_at": timestamp_sql,
		},
	)

	_ensure_table(
		schema_editor,
		connection,
		"notas_profesoras_clases",
		"""
		CREATE TABLE notas_profesoras_clases (
			id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
			class_session_id integer NOT NULL,
			teacher_id char(32) NOT NULL,
			note text NOT NULL DEFAULT '',
			updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
			created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
		)
		""",
		"""
		CREATE TABLE notas_profesoras_clases (
			id bigserial NOT NULL PRIMARY KEY,
			class_session_id bigint NOT NULL,
			teacher_id uuid NOT NULL,
			note text NOT NULL DEFAULT '',
			updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
			created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
		)
		""",
	)
	_ensure_columns(
		schema_editor,
		connection,
		"notas_profesoras_clases",
		{
			"class_session_id": session_fk_sql,
			"teacher_id": user_fk_sql,
			"note": "text NOT NULL DEFAULT ''",
			"updated_at": timestamp_sql,
			"created_at": timestamp_sql,
		},
	)


class Migration(migrations.Migration):
	dependencies = [
		("core", "0007_sync_class_credit_adjustments"),
	]

	operations = [
		migrations.RunPython(sync_teacher_workspace, migrations.RunPython.noop),
	]

