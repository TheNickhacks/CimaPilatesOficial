from django.core.management.base import BaseCommand

from accounts.models import User, UserRole


class Command(BaseCommand):
	help = "Crea/actualiza usuarios de prueba (administrador y profesor) para revisar dashboards."

	def add_arguments(self, parser):
		parser.add_argument(
			"--password",
			type=str,
			default="CimaPilates2026!",
			help="Password a asignar a las cuentas de prueba.",
		)
		parser.add_argument(
			"--admin-email",
			type=str,
			default="test.admin@cimapilates.cl",
			help="Email para el usuario administrador.",
		)
		parser.add_argument(
			"--teacher-email",
			type=str,
			default="test.profesor@cimapilates.cl",
			help="Email para el usuario profesor.",
		)

	def handle(self, *args, **options):
		password = str(options["password"])
		admin_email = str(options["admin_email"]).strip().lower()
		teacher_email = str(options["teacher_email"]).strip().lower()

		admin_user = self._upsert_user(
			email=admin_email,
			password=password,
			role=UserRole.ADMIN,
			nombre="Admin",
			apellido="Cima",
		)
		teacher_user = self._upsert_user(
			email=teacher_email,
			password=password,
			role=UserRole.TEACHER,
			nombre="Profe",
			apellido="Cima",
		)

		self.stdout.write("OK")
		self.stdout.write(f"ADMIN_EMAIL|{admin_user.email}")
		self.stdout.write(f"TEACHER_EMAIL|{teacher_user.email}")
		self.stdout.write("PASSWORD|[el mismo que pasaste en --password]")

	def _upsert_user(self, email, password, role, nombre, apellido):
		user = User.objects.filter(email=email).first()
		if user is None:
			user = User.objects.create_user(
				email=email,
				password=password,
				role=role,
				nombre=nombre,
				apellido=apellido,
				is_active=True,
			)
			return user

		user.role = role
		user.nombre = nombre
		user.apellido = apellido
		user.is_active = True
		user.set_password(password)
		user.save()
		return user

