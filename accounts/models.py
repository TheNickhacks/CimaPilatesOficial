from datetime import date
from uuid import uuid4

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import BaseUserManager
from django.core.files.storage import default_storage
from django.db import models
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
	ADMIN = "administrador", _("Administrador")
	RECEPTION = "recepcionista", _("Recepcionista")
	TEACHER = "profesor", _("Profesor")
	STUDENT = "alumna", _("Alumna")


class UserManager(BaseUserManager):
	use_in_migrations = False

	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError("El correo electrónico es obligatorio")
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault("role", UserRole.ADMIN)
		extra_fields.setdefault("is_active", True)
		return self.create_user(email, password, **extra_fields)


class User(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
	email = models.EmailField(max_length=100, unique=True)
	password_hash = models.CharField(max_length=255)
	nombre = models.CharField(max_length=100, null=True, blank=True)
	apellido = models.CharField(max_length=100, null=True, blank=True)
	nombre_completo = models.CharField(max_length=100, null=True, blank=True)
	rut = models.CharField(max_length=15, unique=True, null=True, blank=True)
	fecha_nacimiento = models.DateField(null=True, blank=True)
	genero = models.CharField(max_length=20, null=True, blank=True)
	telefono = models.CharField(max_length=20, null=True, blank=True)
	informacion_salud = models.TextField(null=True, blank=True)
	consideraciones_clase = models.TextField(null=True, blank=True)
	contacto_emergencia = models.CharField(max_length=100, null=True, blank=True)
	telefono_emergencia = models.CharField(max_length=20, null=True, blank=True)
	role = models.CharField(
		max_length=20,
		choices=UserRole.choices,
		default=UserRole.STUDENT,
		db_column="rol",
	)
	consentimiento_marketing = models.BooleanField(default=False)
	fecha_consentimiento = models.DateTimeField(null=True, blank=True)
	solicitud_eliminacion_datos = models.BooleanField(default=False)
	fecha_solicitud_eliminacion = models.DateTimeField(null=True, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	foto_perfil_path = models.CharField(max_length=255, null=True, blank=True)
	foto_perfil_mime_type = models.CharField(max_length=100, null=True, blank=True)

	USERNAME_FIELD = "email"
	REQUIRED_FIELDS: list[str] = []

	objects = UserManager()

	class Meta:
		managed = False
		db_table = "usuarios"

	@property
	def is_staff(self) -> bool:
		return self.role == UserRole.ADMIN

	@property
	def is_superuser(self) -> bool:
		return self.role == UserRole.ADMIN

	@property
	def is_authenticated(self) -> bool:
		return True

	@property
	def is_anonymous(self) -> bool:
		return False

	def set_password(self, raw_password: str | None) -> None:
		self.password_hash = make_password(raw_password)

	def check_password(self, raw_password: str) -> bool:
		return check_password(raw_password, self.password_hash)

	def get_session_auth_hash(self) -> str:
		return salted_hmac("accounts.User", self.password_hash).hexdigest()

	def get_session_auth_fallback_hash(self):
		from django.conf import settings
		for fallback_secret in getattr(settings, "SECRET_KEY_FALLBACKS", []):
			yield salted_hmac("accounts.User", self.password_hash, secret=fallback_secret).hexdigest()

	def get_username(self) -> str:
		return self.email or ""

	def has_perm(self, perm, obj=None) -> bool:
		return self.is_staff

	def has_module_perms(self, app_label) -> bool:
		return self.is_staff

	@property
	def seniority_days(self) -> int:
		return (date.today() - self.created_at.date()).days

	@property
	def seniority_months(self) -> int:
		return self.seniority_days // 30

	@property
	def loyalty_badge(self) -> str:
		return "NEW"

	@property
	def consecutive_active_plan_months(self) -> int:
		return 0

	def get_full_name(self) -> str:
		if self.nombre or self.apellido:
			return f"{self.nombre or ''} {self.apellido or ''}".strip()
		return self.nombre_completo or ""

	def get_short_name(self) -> str:
		if self.nombre:
			return self.nombre.strip()
		full_name = self.get_full_name().strip()
		return full_name.split(" ")[0] if full_name else ""

	@property
	def profile_initials(self) -> str:
		parts = [part for part in (self.nombre, self.apellido) if part]
		if not parts and self.nombre_completo:
			parts = self.nombre_completo.split()
		return "".join(part[0].upper() for part in parts[:2]) or "CP"

	@property
	def profile_photo_url(self) -> str | None:
		if not self.foto_perfil_path:
			return None
		try:
			return default_storage.url(self.foto_perfil_path)
		except Exception:
			return None

	def __str__(self) -> str:
		return f"{self.get_full_name() or self.email} ({self.get_role_display()})"
