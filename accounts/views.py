from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone

from .forms import EmailLoginForm, StudentProfileForm, StudentSignUpForm, PasswordResetByRutForm


def _store_pending_plan_selection(request):
	plan = request.GET.get("plan")
	period = request.GET.get("period")
	if plan:
		request.session["pending_plan_selection"] = {
			"plan": plan,
			"period": period or "monthly",
			"open_plan": "1",
		}


def _post_auth_redirect(request):
	next_url = request.POST.get("next") or request.GET.get("next")
	if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
		return next_url

	pending_plan = request.session.pop("pending_plan_selection", None)
	if pending_plan:
		return f"{reverse('core:student_dashboard')}?{urlencode(pending_plan)}"

	return reverse("core:dashboard_redirect")


def login_view(request):
	if request.user.is_authenticated:
		return redirect("core:dashboard_redirect")
	_store_pending_plan_selection(request)

	if request.method == "POST":
		form = EmailLoginForm(request.POST)
		if form.is_valid():
			user = form.get_user()
			user.backend = "accounts.backends.EmailBackend"
			login(request, user)
			if not form.cleaned_data.get("remember_me"):
				request.session.set_expiry(0)
			messages.success(request, "Bienvenida/o de nuevo.")
			return redirect(_post_auth_redirect(request))
	else:
		form = EmailLoginForm()

	return render(request, "accounts/login.html", {"form": form, "next": request.GET.get("next", "")})


def signup_student(request):
	if request.user.is_authenticated:
		return redirect("core:dashboard_redirect")
	_store_pending_plan_selection(request)

	if request.method == "POST":
		form = StudentSignUpForm(request.POST)
		if form.is_valid():
			user = form.save()
			authenticated_user = authenticate(username=user.email, password=form.cleaned_data["password1"])
			if authenticated_user is None:
				authenticated_user = user
				authenticated_user.backend = "accounts.backends.EmailBackend"
			login(request, authenticated_user)
			messages.success(request, "Tu cuenta fue creada correctamente.")
			return redirect(_post_auth_redirect(request))
	else:
		form = StudentSignUpForm()

	return render(request, "accounts/signup.html", {"form": form, "next": request.GET.get("next", "")})


def terms_view(request):
	return render(request, "accounts/terms.html")


def logout_view(request):
	logout(request)
	messages.info(request, "Sesión cerrada correctamente.")
	return redirect("core:home")


@login_required
def profile(request):
	if request.method == "POST":
		action = request.POST.get("action")
		if action == "update_profile":
			form = StudentProfileForm(request.POST, request.FILES, user=request.user)
			if form.is_valid():
				form.save()
				if form.cleaned_data.get("password1"):
					update_session_auth_hash(request, request.user)
				messages.success(request, "Tu perfil fue actualizado correctamente.")
				return redirect("accounts:profile")
		else:
			form = StudentProfileForm(
				initial={
					"nombre": request.user.nombre,
					"apellido": request.user.apellido,
					"nombre_completo": request.user.nombre_completo,
					"rut": request.user.rut,
					"email": request.user.email,
					"telefono": request.user.telefono,
					"informacion_salud": request.user.informacion_salud,
					"consideraciones_clase": request.user.consideraciones_clase,
					"contacto_emergencia": request.user.contacto_emergencia,
					"telefono_emergencia": request.user.telefono_emergencia,
					"fecha_nacimiento": request.user.fecha_nacimiento,
					"genero": request.user.genero,
					"consentimiento_marketing": request.user.consentimiento_marketing,
				},
				user=request.user,
			)

			if action == "request_data_deletion":
				if not request.user.solicitud_eliminacion_datos:
					request.user.solicitud_eliminacion_datos = True
					request.user.fecha_solicitud_eliminacion = timezone.now()
					request.user.save(update_fields=["solicitud_eliminacion_datos", "fecha_solicitud_eliminacion"])
				messages.success(
					request,
					"Registramos tu solicitud de eliminacion de datos personales. El equipo revisara el requerimiento segun la Ley 21.719.",
				)
				return redirect("accounts:profile")

			if action == "delete_account":
				if request.POST.get("confirm_delete") != "1":
					messages.error(request, "Debes confirmar la desactivacion de la cuenta antes de continuar.")
					return redirect("accounts:profile")
				request.user.is_active = False
				request.user.save(update_fields=["is_active"])
				logout(request)
				messages.info(request, "Tu cuenta fue desactivada correctamente.")
				return redirect("core:home")
	else:
		form = StudentProfileForm(
			initial={
				"nombre": request.user.nombre,
				"apellido": request.user.apellido,
				"nombre_completo": request.user.nombre_completo,
				"rut": request.user.rut,
				"email": request.user.email,
				"telefono": request.user.telefono,
				"informacion_salud": request.user.informacion_salud,
				"consideraciones_clase": request.user.consideraciones_clase,
				"contacto_emergencia": request.user.contacto_emergencia,
				"telefono_emergencia": request.user.telefono_emergencia,
				"fecha_nacimiento": request.user.fecha_nacimiento,
				"genero": request.user.genero,
				"consentimiento_marketing": request.user.consentimiento_marketing,
			},
			user=request.user,
		)

	return render(request, "accounts/profile.html", {"form": form})


def reset_password(request):
	if request.user.is_authenticated:
		return redirect("core:dashboard_redirect")

	if request.method == "POST":
		form = PasswordResetByRutForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, "Tu contraseña ha sido restablecida correctamente. Ya puedes iniciar sesión.")
			return redirect("accounts:login")
	else:
		form = PasswordResetByRutForm()

	return render(request, "accounts/reset_password.html", {"form": form})

