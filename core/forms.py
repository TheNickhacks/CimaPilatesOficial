from pathlib import Path
from uuid import uuid4

from django import forms
from django.core.files.storage import default_storage

from .models import (
	ClassSession,
	LandingLead,
	PaymentMethod,
	PlanBillingPeriod,
	PlanCatalog,
	PlanRequest,
	SingleClassBooking,
	SingleClassBookingStatus,
)
from utils.rut import normalize_rut


class LandingLeadForm(forms.Form):
	nombre = forms.CharField(max_length=100, label="Nombre Completo")
	rut = forms.CharField(max_length=15, label="RUT")
	email = forms.EmailField(max_length=100, label="Correo electrónico")
	telefono = forms.CharField(max_length=20, label="Teléfono")

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		field_classes = (
			"mt-2 block w-full rounded-2xl border border-olive/15 bg-ivory px-4 py-3 "
			"text-sm text-charcoal outline-none transition focus:border-olive focus:ring-2 focus:ring-olive/10"
		)
		self.fields["nombre"].widget.attrs.update({"class": field_classes, "autocomplete": "name"})
		self.fields["rut"].widget.attrs.update({"class": field_classes, "autocomplete": "off"})
		self.fields["email"].widget.attrs.update({"class": field_classes, "autocomplete": "email"})
		self.fields["telefono"].widget.attrs.update({"class": field_classes, "autocomplete": "tel"})

	def clean_rut(self):
		return normalize_rut(self.cleaned_data["rut"])

	def clean_email(self):
		email = self.cleaned_data["email"].strip().lower()
		if LandingLead.objects.filter(email__iexact=email).exists():
			raise forms.ValidationError("Este correo ya está registrado en la lista de espera.")
		return email

	def save(self):
		return LandingLead.objects.create(
			nombre=self.cleaned_data["nombre"].strip(),
			rut=self.cleaned_data["rut"],
			email=self.cleaned_data["email"].strip().lower(),
			telefono=self.cleaned_data["telefono"].strip(),
		)


class PlanRequestForm(forms.Form):
	plan_slug = forms.CharField(widget=forms.HiddenInput())
	periodo = forms.ChoiceField(
		label="Periodo del plan",
		choices=PlanBillingPeriod.choices,
		initial=PlanBillingPeriod.MONTHLY,
	)
	metodo_pago = forms.ChoiceField(
		label="Forma de pago",
		choices=PaymentMethod.choices,
		initial=PaymentMethod.IN_STUDIO,
	)
	notas = forms.CharField(
		label="Notas adicionales",
		required=False,
		widget=forms.Textarea(attrs={"rows": 3}),
	)
	comprobante = forms.FileField(label="Subir comprobante", required=False)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		field_classes = (
			"mt-2 block w-full rounded-2xl border border-olive/15 bg-ivory px-4 py-3 "
			"text-sm text-charcoal outline-none transition focus:border-olive focus:ring-2 focus:ring-olive/10"
		)
		self.fields["periodo"].widget.attrs.update({"class": field_classes})
		self.fields["metodo_pago"].widget.attrs.update({"class": field_classes})
		self.fields["notas"].widget.attrs.update({"class": field_classes})
		self.fields["comprobante"].widget.attrs.update(
			{
				"class": "mt-2 block w-full rounded-2xl border border-dashed border-olive/20 bg-ivory px-4 py-3 text-sm text-charcoal",
				"accept": ".pdf,.png,.jpg,.jpeg,.webp",
			}
		)
		self.plan = None

	def clean_plan_slug(self):
		slug = self.cleaned_data["plan_slug"].strip()
		plan = PlanCatalog.objects.filter(slug=slug, activo=True, es_clase_suelta=False).first()
		if plan is None:
			raise forms.ValidationError("El plan seleccionado no está disponible.")
		self.plan = plan
		return slug

	def clean(self):
		return super().clean()

	def save(self, user):
		from django.utils import timezone
		from datetime import timedelta
		five_minutes_ago = timezone.now() - timedelta(minutes=5)
		if PlanRequest.objects.filter(user=user, created_at__gte=five_minutes_ago).exists():
			raise forms.ValidationError("Ya has enviado una solicitud de plan recientemente. Por favor espera al menos 5 minutos entre cada solicitud.")

		comprobante = self.files.get("comprobante")
		comprobante_path = None
		if comprobante:
			extension = Path(comprobante.name).suffix.lower()
			filename = f"comprobantes/{user.id}/{uuid4().hex}{extension}"
			comprobante_path = default_storage.save(filename, comprobante)
		return PlanRequest.objects.create(
			user=user,
			plan=self.plan,
			periodo=self.cleaned_data["periodo"],
			metodo_pago=self.cleaned_data["metodo_pago"],
			detalle_transferencia=None,
			notas=(self.cleaned_data.get("notas") or "").strip() or None,
			comprobante_path=comprobante_path,
		)


class ClassReservationForm(forms.Form):
	session_id = forms.IntegerField(widget=forms.HiddenInput())
	nota = forms.CharField(
		label="Nota opcional",
		required=False,
		widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Si quieres, deja una observacion para esta reserva."}),
	)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields["nota"].widget.attrs.update(
			{
				"class": "mt-2 block w-full rounded-2xl border border-olive/15 bg-ivory px-4 py-3 text-sm text-charcoal outline-none transition focus:border-olive focus:ring-2 focus:ring-olive/10",
			}
		)
		self.session = None

	def clean_session_id(self):
		session_id = self.cleaned_data["session_id"]
		self.session = ClassSession.objects.filter(pk=session_id).first()
		if self.session is None:
			raise forms.ValidationError("La clase seleccionada ya no esta disponible.")
		return session_id

	def clean_nota(self):
		return (self.cleaned_data.get("nota") or "").strip()


class SingleClassPublicBookingForm(forms.Form):
	session_id = forms.IntegerField(widget=forms.HiddenInput())
	tipo_clase = forms.CharField(widget=forms.HiddenInput(), initial="prueba", required=False)
	nombre = forms.CharField(max_length=100, label="Nombre")
	apellido = forms.CharField(max_length=100, label="Apellido", required=False)
	rut = forms.CharField(max_length=15, label="RUT")
	email = forms.EmailField(max_length=100, label="Correo electronico")
	telefono = forms.CharField(max_length=20, label="Telefono")
	edad = forms.IntegerField(
		label="Edad",
		required=True,
		min_value=1,
		widget=forms.NumberInput(attrs={"placeholder": "Ej: 28"}),
	)
	operaciones_lesiones = forms.CharField(
		label="¿Tienes operaciones o lesiones recientes?",
		required=False,
		widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Describe si has tenido cirugías, fracturas, hernias, etc."}),
	)
	condiciones_medicas = forms.CharField(
		label="Condiciones médicas o de salud importantes",
		required=False,
		widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Indica si tienes hipertensión, dolores crónicos, embarazo, etc."}),
	)
	metodo_pago = forms.ChoiceField(
		label="Forma de pago",
		choices=[
			("transferencia", "Transferencia bancaria"),
			("link_pago", "Link de pago (SumUp)"),
		],
		initial="transferencia",
	)
	notas = forms.CharField(
		label="Notas adicionales",
		required=False,
		widget=forms.Textarea(attrs={"rows": 3}),
	)
	comprobante = forms.FileField(label="Subir comprobante", required=False)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		field_classes = (
			"mt-2 block w-full rounded-2xl border border-olive/15 bg-ivory px-4 py-3 "
			"text-sm text-charcoal outline-none transition focus:border-olive focus:ring-2 focus:ring-olive/10"
		)
		for field_name in ("nombre", "apellido", "rut", "email", "telefono", "metodo_pago", "notas", "edad", "operaciones_lesiones", "condiciones_medicas"):
			self.fields[field_name].widget.attrs.update({"class": field_classes})
		self.fields["metodo_pago"].widget.attrs.update({"x-model": "metodo"})
		self.fields["comprobante"].widget.attrs.update(
			{
				"class": "mt-2 block w-full rounded-2xl border border-dashed border-olive/20 bg-ivory px-4 py-3 text-sm text-charcoal",
				"accept": ".pdf,.png,.jpg,.jpeg,.webp",
			}
		)
		self.session = None

	def clean_session_id(self):
		session_id = self.cleaned_data["session_id"]
		self.session = ClassSession.objects.filter(pk=session_id).first()
		if self.session is None:
			raise forms.ValidationError("La clase seleccionada ya no esta disponible.")
		return session_id

	def clean_tipo_clase(self):
		tipo = (self.cleaned_data.get("tipo_clase") or "prueba").strip().lower()
		if tipo not in {"prueba", "suelta"}:
			tipo = "prueba"
		return tipo

	def clean_rut(self):
		return normalize_rut(self.cleaned_data["rut"])

	def clean_email(self):
		return self.cleaned_data["email"].strip().lower()

	def clean(self):
		cleaned_data = super().clean()
		if self.session is None:
			return cleaned_data
		email = cleaned_data.get("email")
		rut = cleaned_data.get("rut")
		tipo_clase = cleaned_data.get("tipo_clase") or "prueba"
		is_trial = (tipo_clase == "prueba")

		if is_trial:
			from datetime import time, timezone as dt_timezone
			from django.utils import timezone
			from .models import SystemSetting
			allow_pm_trials = (SystemSetting.get_setting("allow_pm_trial_classes", "false").lower() == "true")
			session_dt = self.session.starts_at
			if timezone.is_naive(session_dt):
				session_local = timezone.localtime(session_dt.replace(tzinfo=dt_timezone.utc), timezone.get_current_timezone())
			else:
				session_local = timezone.localtime(session_dt, timezone.get_current_timezone())
			if session_local.weekday() < 5 and session_local.time() >= time(12, 0) and not allow_pm_trials:
				msg = "Las clases de prueba ($5.000) sólo están habilitadas para horario AM y Sábados."
				self.add_error("session_id", msg)
				self.add_error(None, msg)

		if email:
			if is_trial:
				if SingleClassBooking.objects.filter(
					email__iexact=email,
					tipo_clase="prueba",
					estado__in=(SingleClassBookingStatus.PENDING, SingleClassBookingStatus.CONFIRMED),
				).exists():
					self.add_error("email", "La clase de prueba ($5.000) está limitada a 1 por correo electrónico.")
			else:
				if SingleClassBooking.objects.filter(
					class_session=self.session,
					email__iexact=email,
					estado__in=(SingleClassBookingStatus.PENDING, SingleClassBookingStatus.CONFIRMED),
				).exists():
					self.add_error("email", "Ya existe una solicitud activa para esta clase con este correo.")

		if rut:
			if is_trial:
				if SingleClassBooking.objects.filter(
					rut=rut,
					tipo_clase="prueba",
					estado__in=(SingleClassBookingStatus.PENDING, SingleClassBookingStatus.CONFIRMED),
				).exists():
					self.add_error("rut", "La clase de prueba ($5.000) está limitada a 1 por RUT.")
			else:
				if SingleClassBooking.objects.filter(
					class_session=self.session,
					rut=rut,
					estado__in=(SingleClassBookingStatus.PENDING, SingleClassBookingStatus.CONFIRMED),
				).exists():
					self.add_error("rut", "Ya existe una solicitud activa para esta clase con este RUT.")
		return cleaned_data

	def save(self):
		comprobante = self.files.get("comprobante")
		comprobante_path = None
		if comprobante:
			extension = Path(comprobante.name).suffix.lower()
			filename = f"comprobantes/clase-suelta/{uuid4().hex}{extension}"
			comprobante_path = default_storage.save(filename, comprobante)
		return SingleClassBooking.objects.create(
			class_session=self.session,
			nombre=self.cleaned_data["nombre"].strip(),
			apellido=(self.cleaned_data.get("apellido") or "").strip() or None,
			rut=self.cleaned_data["rut"],
			email=self.cleaned_data["email"],
			telefono=self.cleaned_data["telefono"].strip(),
			edad=self.cleaned_data["edad"],
			operaciones_lesiones=(self.cleaned_data.get("operaciones_lesiones") or "").strip() or None,
			condiciones_medicas=(self.cleaned_data.get("condiciones_medicas") or "").strip() or None,
			metodo_pago=self.cleaned_data["metodo_pago"],
			notas=(self.cleaned_data.get("notas") or "").strip() or None,
			comprobante_path=comprobante_path,
			tipo_clase=self.cleaned_data.get("tipo_clase") or "prueba",
		)
