from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("agenda/clase-suelta/", views.public_single_class_booking, name="public_single_class_booking"),
    path("agenda/confirmar/<str:token>/", views.confirm_class_reservation, name="confirm_class_reservation"),
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
    path("dashboard/alumna/", views.student_dashboard, name="student_dashboard"),
    path("dashboard/alumna/agenda/", views.student_schedule, name="student_schedule"),
    path("dashboard/profesor/", views.teacher_dashboard, name="teacher_dashboard"),
    path("dashboard/recepcion/", views.teacher_dashboard, name="reception_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
]
