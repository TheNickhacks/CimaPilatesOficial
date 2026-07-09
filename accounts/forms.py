from pathlib import Path
from uuid import uuid4

from django import forms
from django.core.files.storage import default_storage
from django.utils import timezone

from .models import User, UserRole
from utils.rut import normalize_rut


class StudentSignUpForm(forms.Form):
    nombre = forms.CharField(max_length=100, label="Nombre")
    apellido = forms.CharField(max_length=100, label="Apellido")
    rut = forms.CharField(max_length=15, label="RUT")
    email = forms.EmailField(label="Correo")
    telefono = forms.CharField(max_length=20, label="Teléfono")
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)
    acepta_terminos = forms.BooleanField(
        required=True,
        label="Acepto los términos y condiciones y el tratamiento de mis datos personales.",
        error_messages={"required": "Debes aceptar los términos y el tratamiento de datos para registrarte."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_classes = (
            "mt-2 block w-full rounded-2xl border border-olive/15 bg-ivory px-4 py-3 "
            "text-sm text-charcoal outline-none transition focus:border-olive focus:ring-2 focus:ring-olive/10"
        )
        self.fields["nombre"].widget.attrs.update({"autocomplete": "given-name", "class": field_classes})
        self.fields["apellido"].widget.attrs.update({"autocomplete": "family-name", "class": field_classes})
        self.fields["rut"].widget.attrs.update({"autocomplete": "off", "class": field_classes})
        self.fields["email"].widget.attrs.update({"autocomplete": "email", "class": field_classes})
        self.fields["telefono"].widget.attrs.update({"autocomplete": "tel", "class": field_classes})
        self.fields["password1"].widget.attrs.update({"autocomplete": "new-password", "class": field_classes})
        self.fields["password2"].widget.attrs.update({"autocomplete": "new-password", "class": field_classes})
        self.fields["acepta_terminos"].widget.attrs.update(
            {
                "class": "mt-1 h-4 w-4 rounded border-olive/30 text-olive focus:ring-olive/20",
            }
        )

    def clean_rut(self):
        rut = normalize_rut(self.cleaned_data["rut"])
        if User.objects.filter(rut=rut).exists():
            raise forms.ValidationError("Ya existe una cuenta con este RUT.")
        return rut

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        nombre = self.cleaned_data["nombre"].strip()
        apellido = self.cleaned_data["apellido"].strip()
        full_name = f"{nombre} {apellido}".strip()
        consentimiento_fecha = timezone.now()
        user = User(
            email=self.cleaned_data["email"],
            nombre=nombre,
            apellido=apellido,
            nombre_completo=full_name,
            rut=self.cleaned_data["rut"],
            telefono=self.cleaned_data["telefono"],
            role=UserRole.STUDENT,
            consentimiento_marketing=True,
            fecha_consentimiento=consentimiento_fecha,
        )
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        label="Correo",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    remember_me = forms.BooleanField(required=False, label="Recordarme")

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if not email or not password:
            return cleaned_data

        user = User.objects.filter(email__iexact=email.strip()).first()
        if user is None or not user.check_password(password):
            raise forms.ValidationError("Correo o contraseña incorrectos.")
        if not user.is_active:
            raise forms.ValidationError("Tu cuenta está desactivada.")

        self.user_cache = user
        return cleaned_data

    def get_user(self):
        return getattr(self, "user_cache", None)


class StudentProfileForm(forms.Form):
    nombre = forms.CharField(max_length=100, label="Nombre", required=False)
    apellido = forms.CharField(max_length=100, label="Apellido", required=False)
    nombre_completo = forms.CharField(max_length=100, label="Nombre completo", required=False)
    rut = forms.CharField(max_length=15, label="RUT", required=False)
    email = forms.EmailField(label="Correo")
    telefono = forms.CharField(max_length=20, label="Telefono", required=False)
    informacion_salud = forms.CharField(
        label="Informacion de salud relevante",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    consideraciones_clase = forms.CharField(
        label="Consideraciones para tus clases",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    contacto_emergencia = forms.CharField(max_length=100, label="Contacto de emergencia", required=False)
    telefono_emergencia = forms.CharField(max_length=20, label="Telefono de emergencia", required=False)
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    genero = forms.CharField(max_length=20, label="Genero", required=False)
    consentimiento_marketing = forms.BooleanField(
        required=False,
        label="Acepto recibir comunicaciones e informacion comercial de Cima Pilates.",
    )
    foto_perfil = forms.FileField(label="Foto de perfil", required=False)
    password1 = forms.CharField(label="Nueva contrasena", required=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar nueva contrasena", required=False, widget=forms.PasswordInput)

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        field_classes = (
            "mt-2 block w-full rounded-2xl border border-olive/15 bg-ivory px-4 py-3 "
            "text-sm text-charcoal outline-none transition focus:border-olive focus:ring-2 focus:ring-olive/10"
        )
        for field_name in (
            "nombre",
            "apellido",
            "nombre_completo",
            "rut",
            "email",
            "telefono",
            "informacion_salud",
            "consideraciones_clase",
            "contacto_emergencia",
            "telefono_emergencia",
            "fecha_nacimiento",
            "genero",
            "password1",
            "password2",
        ):
            self.fields[field_name].widget.attrs.update({"class": field_classes})
        self.fields["foto_perfil"].widget.attrs.update(
            {
                "class": "mt-2 block w-full rounded-2xl border border-dashed border-olive/20 bg-ivory px-4 py-3 text-sm text-charcoal",
                "accept": ".png,.jpg,.jpeg,.webp",
            }
        )
        self.fields["consentimiento_marketing"].widget.attrs.update(
            {
                "class": "mt-1 h-4 w-4 rounded border-olive/30 text-olive focus:ring-olive/20",
            }
        )

    def clean_rut(self):
        rut = (self.cleaned_data.get("rut") or "").strip()
        if not rut:
            return ""
        rut = normalize_rut(rut)
        if User.objects.exclude(pk=self.user.pk).filter(rut=rut).exists():
            raise forms.ValidationError("Ya existe otra cuenta con este RUT.")
        return rut

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe otra cuenta con este correo.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "Las contrasenas no coinciden.")
            elif len(password1 or "") < 8:
                self.add_error("password1", "La contrasena debe tener al menos 8 caracteres.")
        return cleaned_data

    def save(self):
        nombre = (self.cleaned_data.get("nombre") or "").strip()
        apellido = (self.cleaned_data.get("apellido") or "").strip()
        nombre_completo = (self.cleaned_data.get("nombre_completo") or "").strip() or f"{nombre} {apellido}".strip()

        self.user.nombre = nombre or None
        self.user.apellido = apellido or None
        self.user.nombre_completo = nombre_completo or None
        self.user.rut = self.cleaned_data.get("rut") or None
        self.user.email = self.cleaned_data["email"]
        self.user.telefono = (self.cleaned_data.get("telefono") or "").strip() or None
        self.user.informacion_salud = (self.cleaned_data.get("informacion_salud") or "").strip() or None
        self.user.consideraciones_clase = (self.cleaned_data.get("consideraciones_clase") or "").strip() or None
        self.user.contacto_emergencia = (self.cleaned_data.get("contacto_emergencia") or "").strip() or None
        self.user.telefono_emergencia = (self.cleaned_data.get("telefono_emergencia") or "").strip() or None
        self.user.fecha_nacimiento = self.cleaned_data.get("fecha_nacimiento")
        self.user.genero = (self.cleaned_data.get("genero") or "").strip() or None

        consentimiento_marketing = self.cleaned_data.get("consentimiento_marketing", False)
        if consentimiento_marketing and not self.user.consentimiento_marketing:
            self.user.fecha_consentimiento = timezone.now()
        self.user.consentimiento_marketing = consentimiento_marketing

        password = self.cleaned_data.get("password1")
        if password:
            self.user.set_password(password)

        foto_perfil = self.files.get("foto_perfil")
        if foto_perfil:
            extension = Path(foto_perfil.name).suffix.lower()
            filename = f"perfiles/{self.user.id}/{uuid4().hex}{extension}"
            self.user.foto_perfil_path = default_storage.save(filename, foto_perfil)
            self.user.foto_perfil_mime_type = getattr(foto_perfil, "content_type", "") or None

        self.user.save()
        return self.user


class PasswordResetByRutForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    rut = forms.CharField(max_length=15, label="RUT")
    password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar nueva contraseña", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_classes = (
            "mt-2 block w-full rounded-2xl border border-olive/15 bg-ivory px-4 py-3 "
            "text-sm text-charcoal outline-none transition focus:border-olive focus:ring-2 focus:ring-olive/10"
        )
        self.fields["email"].widget.attrs.update({"autocomplete": "email", "class": field_classes})
        self.fields["rut"].widget.attrs.update({"autocomplete": "off", "class": field_classes})
        self.fields["password1"].widget.attrs.update({"autocomplete": "new-password", "class": field_classes})
        self.fields["password2"].widget.attrs.update({"autocomplete": "new-password", "class": field_classes})

    def clean_rut(self):
        rut_value = (self.cleaned_data.get("rut") or "").strip()
        if not rut_value:
            raise forms.ValidationError("El RUT es obligatorio.")
        try:
            return normalize_rut(rut_value)
        except ValueError as e:
            raise forms.ValidationError(str(e))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        rut = cleaned_data.get("rut")
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if email and rut:
            user = User.objects.filter(email__iexact=email.strip().lower(), rut=rut).first()
            if not user:
                raise forms.ValidationError("No se encontró ningún usuario con ese correo y RUT.")
            if not user.is_active:
                raise forms.ValidationError("La cuenta asociada a este usuario está desactivada.")
            self.user_cache = user

        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            elif len(password1 or "") < 8:
                self.add_error("password1", "La contraseña debe tener al menos 8 caracteres.")

        return cleaned_data

    def save(self):
        user = self.user_cache
        user.set_password(self.cleaned_data["password1"])
        user.save()
        return user

