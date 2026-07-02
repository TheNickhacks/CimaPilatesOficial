"""Core app models mapped to existing Neon tables."""

from django.db import models


class LandingLead(models.Model):
	id = models.BigAutoField(primary_key=True)
	nombre = models.CharField(max_length=100)
	rut = models.CharField(max_length=15, null=True, blank=True)
	email = models.EmailField(max_length=100)
	telefono = models.CharField(max_length=20)
	registered_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = False
		db_table = "landing_leads"

	def __str__(self) -> str:
		return f"{self.nombre} <{self.email}>"


class PlanCatalog(models.Model):
	id = models.BigAutoField(primary_key=True)
	slug = models.SlugField(max_length=50, unique=True)
	nombre = models.CharField(max_length=100)
	icono = models.CharField(max_length=10)
	clases_por_mes = models.PositiveIntegerField()
	frecuencia = models.CharField(max_length=60)
	precio_mensual = models.PositiveIntegerField()
	precio_trimestral = models.PositiveIntegerField()
	precio_semestral = models.PositiveIntegerField()
	es_clase_suelta = models.BooleanField(default=False)
	destacado = models.BooleanField(default=False)
	descripcion = models.CharField(max_length=255, null=True, blank=True)
	activo = models.BooleanField(default=True)
	orden = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		managed = False
		db_table = "planes_catalogo"
		ordering = ("orden", "id")

	def __str__(self) -> str:
		return self.nombre

	@property
	def weekly_class_limit(self) -> int:
		if self.es_clase_suelta:
			return 1
		return max(self.clases_por_mes // 4, 1)


class PlanRequestStatus(models.TextChoices):
	PENDING = "pendiente", "Pendiente"
	UNDER_REVIEW = "en_revision", "En revision"
	CONFIRMED = "confirmado", "Confirmado"
	REJECTED = "rechazado", "Rechazado"


class PlanBillingPeriod(models.TextChoices):
	MONTHLY = "monthly", "Mensual"
	QUARTERLY = "quarterly", "Trimestral"
	SEMESTER = "semester", "Semestral"


class PaymentMethod(models.TextChoices):
	IN_STUDIO = "presencial", "Pago en estudio"
	TRANSFER = "transferencia", "Transferencia"


class PlanRequest(models.Model):
	id = models.BigAutoField(primary_key=True)
	user = models.ForeignKey(
		"accounts.User",
		on_delete=models.CASCADE,
		db_column="user_id",
		related_name="plan_requests",
	)
	plan = models.ForeignKey(
		PlanCatalog,
		on_delete=models.PROTECT,
		db_column="plan_id",
		related_name="requests",
	)
	periodo = models.CharField(max_length=20, choices=PlanBillingPeriod.choices)
	metodo_pago = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.IN_STUDIO)
	detalle_transferencia = models.TextField(null=True, blank=True)
	notas = models.TextField(null=True, blank=True)
	comprobante_path = models.CharField(max_length=255, null=True, blank=True)
	estado = models.CharField(max_length=20, choices=PlanRequestStatus.choices, default=PlanRequestStatus.PENDING)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		managed = False
		db_table = "solicitudes_planes"
		ordering = ("-created_at",)

	def __str__(self) -> str:
		return f"{self.user_id} - {self.plan.nombre} ({self.get_estado_display()})"


class ClassSession(models.Model):
	id = models.BigAutoField(primary_key=True)
	starts_at = models.DateTimeField(unique=True)
	ends_at = models.DateTimeField()
	capacidad_maxima = models.PositiveIntegerField(default=4)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		managed = False
		db_table = "agenda_clases"
		ordering = ("starts_at",)

	def __str__(self) -> str:
		return f"Clase {self.starts_at}"


class ClassReservation(models.Model):
	id = models.BigAutoField(primary_key=True)
	class_session = models.ForeignKey(
		ClassSession,
		on_delete=models.CASCADE,
		db_column="class_session_id",
		related_name="reservations",
	)
	user = models.ForeignKey(
		"accounts.User",
		on_delete=models.CASCADE,
		db_column="user_id",
		related_name="class_reservations",
	)
	nota = models.TextField(null=True, blank=True)
	confirmation_requested_at = models.DateTimeField(null=True, blank=True)
	confirmed_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = False
		db_table = "reservas_clases"
		ordering = ("class_session__starts_at",)
		unique_together = (("class_session", "user"),)

	def __str__(self) -> str:
		return f"{self.user_id} - {self.class_session_id}"


class SingleClassBookingStatus(models.TextChoices):
	PENDING = "pendiente", "Pendiente"
	CONFIRMED = "confirmada", "Confirmada"
	REJECTED = "rechazada", "Rechazada"
	CANCELLED = "cancelada", "Cancelada"


class SingleClassBooking(models.Model):
	id = models.BigAutoField(primary_key=True)
	class_session = models.ForeignKey(
		ClassSession,
		on_delete=models.CASCADE,
		db_column="class_session_id",
		related_name="single_class_bookings",
	)
	nombre = models.CharField(max_length=100)
	apellido = models.CharField(max_length=100, null=True, blank=True)
	rut = models.CharField(max_length=15)
	email = models.EmailField(max_length=100)
	telefono = models.CharField(max_length=20)
	metodo_pago = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.IN_STUDIO)
	notas = models.TextField(null=True, blank=True)
	comprobante_path = models.CharField(max_length=255, null=True, blank=True)
	estado = models.CharField(max_length=20, choices=SingleClassBookingStatus.choices, default=SingleClassBookingStatus.PENDING)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		managed = False
		db_table = "solicitudes_clase_suelta"
		ordering = ("-created_at",)

	def __str__(self) -> str:
		return f"{self.nombre} {self.apellido or ''} - {self.class_session_id}".strip()


class ClassCreditAdjustment(models.Model):
	id = models.BigAutoField(primary_key=True)
	user = models.ForeignKey(
		"accounts.User",
		on_delete=models.CASCADE,
		db_column="user_id",
		related_name="class_credit_adjustments",
	)
	plan_request = models.ForeignKey(
		PlanRequest,
		on_delete=models.CASCADE,
		db_column="plan_request_id",
		related_name="class_credit_adjustments",
		null=True,
		blank=True,
	)
	cantidad = models.IntegerField()
	motivo = models.TextField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = False
		db_table = "ajustes_clases"
		ordering = ("-created_at",)

	def __str__(self) -> str:
		return f"{self.user_id} +{self.cantidad}"


class TeacherShiftKind(models.TextChoices):
	AM = "am", "AM"
	PM = "pm", "PM"
	SATURDAY = "sabado", "Sabado"


class TeacherWorkShift(models.Model):
	id = models.BigAutoField(primary_key=True)
	teacher = models.ForeignKey(
		"accounts.User",
		on_delete=models.CASCADE,
		db_column="teacher_id",
		related_name="teacher_work_shifts",
	)
	shift_date = models.DateField()
	shift_kind = models.CharField(max_length=20, choices=TeacherShiftKind.choices)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = False
		db_table = "turnos_profesoras"
		ordering = ("shift_date", "shift_kind")
		unique_together = (("teacher", "shift_date", "shift_kind"),)

	def __str__(self) -> str:
		return f"{self.teacher_id} - {self.shift_date} - {self.shift_kind}"


class TeacherMonthlyShift(models.Model):
	id = models.BigAutoField(primary_key=True)
	teacher = models.ForeignKey(
		"accounts.User",
		on_delete=models.CASCADE,
		db_column="teacher_id",
		related_name="teacher_monthly_shifts",
	)
	year = models.PositiveIntegerField()
	month = models.PositiveIntegerField()
	shift_kind = models.CharField(max_length=20, choices=TeacherShiftKind.choices)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = False
		db_table = "turnos_profesoras_mensual"
		ordering = ("year", "month", "shift_kind")
		unique_together = (("teacher", "year", "month", "shift_kind"),)

	def __str__(self) -> str:
		return f"{self.teacher_id} - {self.year}-{self.month:02d} - {self.shift_kind}"


class TeacherHoursAdjustment(models.Model):
	id = models.BigAutoField(primary_key=True)
	teacher = models.ForeignKey(
		"accounts.User",
		on_delete=models.CASCADE,
		db_column="teacher_id",
		related_name="teacher_hours_adjustments",
	)
	year = models.PositiveIntegerField()
	month = models.PositiveIntegerField()
	minutes_delta = models.IntegerField()
	reason = models.TextField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = False
		db_table = "ajustes_horas_profesoras"
		ordering = ("-created_at",)

	def __str__(self) -> str:
		return f"{self.teacher_id} {self.year}-{self.month:02d} {self.minutes_delta}m"


class ClassAttendance(models.Model):
	id = models.BigAutoField(primary_key=True)
	class_session = models.ForeignKey(
		ClassSession,
		on_delete=models.CASCADE,
		db_column="class_session_id",
		related_name="attendance_records",
	)
	user = models.ForeignKey(
		"accounts.User",
		on_delete=models.CASCADE,
		db_column="user_id",
		related_name="class_attendance_records",
	)
	teacher = models.ForeignKey(
		"accounts.User",
		on_delete=models.SET_NULL,
		db_column="teacher_id",
		related_name="marked_attendance_records",
		null=True,
		blank=True,
	)
	present = models.BooleanField(default=False)
	marked_at = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = False
		db_table = "asistencias_clases"
		ordering = ("class_session__starts_at", "user__nombre", "user__apellido")
		unique_together = (("class_session", "user"),)

	def __str__(self) -> str:
		return f"{self.class_session_id} - {self.user_id} - {self.present}"


class TeacherSessionNote(models.Model):
	id = models.BigAutoField(primary_key=True)
	class_session = models.ForeignKey(
		ClassSession,
		on_delete=models.CASCADE,
		db_column="class_session_id",
		related_name="teacher_session_notes",
	)
	teacher = models.ForeignKey(
		"accounts.User",
		on_delete=models.CASCADE,
		db_column="teacher_id",
		related_name="teacher_session_notes",
	)
	note = models.TextField()
	updated_at = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		managed = False
		db_table = "notas_profesoras_clases"
		ordering = ("-updated_at",)
		unique_together = (("class_session", "teacher"),)

	def __str__(self) -> str:
		return f"{self.teacher_id} - {self.class_session_id}"
