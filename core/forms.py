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
	nombre = forms.CharField(max_length=100, label="Nombre")
	apellido = forms.CharField(max_length=100, label="Apellido", required=False)
	rut = forms.CharField(max_length=15, label="RUT")
	email = forms.EmailField(max_length=100, label="Correo electronico")
	telefono = forms.CharField(max_length=20, label="Telefono")
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
		for field_name in ("nombre", "apellido", "rut", "email", "telefono", "metodo_pago", "notas"):
			self.fields[field_name].widget.attrs.update({"class": field_classes})
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
		if email and SingleClassBooking.objects.filter(
			class_session=self.session,
			email__iexact=email,
			estado__in=(SingleClassBookingStatus.PENDING, SingleClassBookingStatus.CONFIRMED),
		).exists():
			self.add_error("email", "Ya existe una solicitud activa para esta clase con este correo.")
		if rut and SingleClassBooking.objects.filter(
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
			metodo_pago=self.cleaned_data["metodo_pago"],
			notas=(self.cleaned_data.get("notas") or "").strip() or None,
			comprobante_path=comprobante_path,
		)
