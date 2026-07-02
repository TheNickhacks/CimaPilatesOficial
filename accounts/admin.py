from django.contrib import admin

from .models import User


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
	list_display = ("email", "rut", "nombre", "apellido", "role", "consentimiento_marketing", "fecha_consentimiento", "is_active")
	list_filter = ("role", "is_active", "consentimiento_marketing")
	search_fields = ("email", "nombre", "apellido", "nombre_completo", "rut", "telefono")
