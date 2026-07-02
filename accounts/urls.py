from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("registro/", views.signup_student, name="signup_student"),
    path("terminos-y-condiciones/", views.terms_view, name="terms"),
    path("perfil/", views.profile, name="profile"),
    path("ingresar/", views.login_view, name="login"),
    path("salir/", views.logout_view, name="logout"),
]
