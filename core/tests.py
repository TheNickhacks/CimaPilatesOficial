from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone

from core.forms import SingleClassPublicBookingForm
from core.models import ClassSession, SingleClassBooking, SingleClassBookingStatus, SingleClassType, PlanRequest, PlanCatalog
from accounts.models import User


from utils.rut import normalize_rut


class SingleClassFlowTests(TestCase):
    def setUp(self):
        start = timezone.now() + timedelta(days=1)
        self.session = ClassSession.objects.create(
            starts_at=start,
            ends_at=start + timedelta(hours=1),
            capacidad_maxima=4,
        )

    def test_trial_class_limit_enforced(self):
        # Create an existing trial booking
        SingleClassBooking.objects.create(
            class_session=self.session,
            nombre="Juan",
            rut=normalize_rut("12.345.678-5"),
            email="juan@example.com",
            telefono="+56912345678",
            edad=25,
            tipo_clase=SingleClassType.PRUEBA,
            estado=SingleClassBookingStatus.CONFIRMED,
        )

        # Attempt to book another trial class with same RUT & email
        form_data = {
            "session_id": self.session.id,
            "tipo_clase": "prueba",
            "nombre": "Juan Pedro",
            "rut": "12.345.678-5",
            "email": "juan@example.com",
            "telefono": "+56987654321",
            "edad": 26,
            "metodo_pago": "transferencia",
        }
        form = SingleClassPublicBookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("rut", form.errors)
        self.assertIn("email", form.errors)

    def test_suelta_class_no_lifetime_limit(self):
        # Create an existing trial booking
        SingleClassBooking.objects.create(
            class_session=self.session,
            nombre="Maria",
            rut=normalize_rut("98.765.432-1"),
            email="maria@example.com",
            telefono="+56912345678",
            edad=30,
            tipo_clase=SingleClassType.PRUEBA,
            estado=SingleClassBookingStatus.CONFIRMED,
        )

        # Create a second session for a suelta class
        start2 = timezone.now() + timedelta(days=2)
        session2 = ClassSession.objects.create(
            starts_at=start2,
            ends_at=start2 + timedelta(hours=1),
            capacidad_maxima=4,
        )

        # Book a suelta class for session2 (should succeed even if Maria already had a trial class)
        form_data = {
            "session_id": session2.id,
            "tipo_clase": "suelta",
            "nombre": "Maria",
            "rut": "98.765.432-1",
            "email": "maria@example.com",
            "telefono": "+56912345678",
            "edad": 30,
            "metodo_pago": "transferencia",
        }
        form = SingleClassPublicBookingForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        booking = form.save()
        self.assertEqual(booking.tipo_clase, "suelta")

    def test_comprobante_url_property(self):
        booking = SingleClassBooking(
            comprobante_path="comprobantes/clase-suelta/abc.png"
        )
        self.assertTrue(booking.comprobante_url.endswith("/media/comprobantes/clase-suelta/abc.png"))

        booking_no_proof = SingleClassBooking(comprobante_path=None)
        self.assertIsNone(booking_no_proof.comprobante_url)

    def test_pm_trial_restriction(self):
        # Session in weekday PM (e.g. 17:00 on a Monday)
        now = timezone.now()
        # Find next Monday 17:00
        days_ahead = 0 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = (now + timedelta(days=days_ahead)).replace(hour=17, minute=0, second=0, microsecond=0)
        pm_session = ClassSession.objects.create(
            starts_at=next_monday,
            ends_at=next_monday + timedelta(hours=1),
            capacidad_maxima=4,
        )

        form_data = {
            "session_id": pm_session.id,
            "tipo_clase": "prueba",
            "nombre": "Camila",
            "rut": "18.765.432-1",
            "email": "camila@example.com",
            "telefono": "+56912345678",
            "edad": 28,
            "metodo_pago": "transferencia",
        }
        form = SingleClassPublicBookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("session_id", form.errors)

    def test_receptionist_role_permissions(self):
        from accounts.models import UserRole
        from django.urls import reverse

        receptionist = User.objects.create_user(
            email="recepcion@cimapilates.cl",
            password="Password123!",
            nombre="Valentina",
            apellido="Recepción",
            role=UserRole.RECEPTION,
        )
        self.client.force_login(receptionist)

        # Test dashboard redirect sends receptionists to reception_dashboard
        res = self.client.get(reverse("core:dashboard_redirect"))
        self.assertRedirects(res, reverse("core:reception_dashboard"))

        # Test reception dashboard loads successfully
        res = self.client.get(reverse("core:reception_dashboard"))
        self.assertEqual(res.status_code, 200)

        # Test admin schedule access allowed for receptionist
        res = self.client.get(reverse("core:admin_schedule"))
        self.assertEqual(res.status_code, 200)

        # Test price editing forbidden for receptionist (financial/pricing settings)
        res = self.client.get(reverse("core:admin_plan_pricing"))
        self.assertEqual(res.status_code, 403)

    def test_payment_link_separation_for_trial_and_suelta(self):
        from django.urls import reverse
        PlanCatalog.objects.filter(es_clase_suelta=True).delete()
        PlanCatalog.objects.create(
            nombre="Clase Suelta / Prueba",
            slug="clase-suelta",
            icono="🌿",
            clases_por_mes=1,
            frecuencia="1 clase",
            precio_mensual=9990,
            precio_trimestral=0,
            precio_semestral=0,
            es_clase_suelta=True,
            activo=True,
            link_pago_prueba="https://pay.sumup.com/b2c/TEST_PRUEBA_LINK",
            link_pago_suelta="https://pay.sumup.com/b2c/TEST_SUELTA_LINK",
        )

        # 1. Request Trial Class flow (?tipo=prueba)
        res_prueba = self.client.get(f"{reverse('core:public_single_class_booking')}?tipo=prueba")
        self.assertEqual(res_prueba.status_code, 200)
        self.assertTrue(res_prueba.context["is_trial"])
        self.assertEqual(res_prueba.context["tipo_clase"], "prueba")
        self.assertContains(res_prueba, "https://pay.sumup.com/b2c/TEST_PRUEBA_LINK")
        self.assertNotContains(res_prueba, "https://pay.sumup.com/b2c/TEST_SUELTA_LINK")

        # 2. Request Single Class flow (?tipo=suelta)
        res_suelta = self.client.get(f"{reverse('core:public_single_class_booking')}?tipo=suelta")
        self.assertEqual(res_suelta.status_code, 200)
        self.assertFalse(res_suelta.context["is_trial"])
        self.assertEqual(res_suelta.context["tipo_clase"], "suelta")
        self.assertContains(res_suelta, "https://pay.sumup.com/b2c/TEST_SUELTA_LINK")
        self.assertNotContains(res_suelta, "https://pay.sumup.com/b2c/TEST_PRUEBA_LINK")


class PlanRenewalFlowTests(TestCase):
    def setUp(self):
        from accounts.models import UserRole
        from core.forms import PlanRequestForm
        from core.models import PlanBillingPeriod, PaymentMethod, PlanRequestStatus
        self.student = User.objects.create_user(
            email="alumna@example.com",
            password="Password123!",
            nombre="Valentina",
            apellido="Prueba",
            role=UserRole.STUDENT,
        )
        self.plan = PlanCatalog.objects.create(
            nombre="Plan Reformer Estándar",
            slug="reformer-estandar",
            icono="🧘",
            clases_por_mes=8,
            frecuencia="2 clases/semana",
            precio_mensual=50000,
            precio_trimestral=135000,
            precio_semestral=250000,
            es_clase_suelta=False,
            activo=True,
            orden=1,
        )
        self.client.force_login(self.student)

    def test_plan_request_form_rate_limit_handled_gracefully(self):
        from core.forms import PlanRequestForm
        from django.urls import reverse

        # First request succeeds
        form_data = {
            "plan_slug": self.plan.slug,
            "periodo": "monthly",
            "metodo_pago": "presencial",
            "notas": "Primera solicitud",
        }
        form1 = PlanRequestForm(data=form_data, user=self.student)
        self.assertTrue(form1.is_valid(), form1.errors)
        form1.save()

        # Second request within 5 minutes should fail validation gracefully without 500 error
        form2 = PlanRequestForm(data=form_data, user=self.student)
        self.assertFalse(form2.is_valid())
        self.assertIn("Ya has enviado una solicitud de plan recientemente", str(form2.errors))

    def test_student_dashboard_preselects_active_plan(self):
        from django.urls import reverse
        from core.models import PlanRequest, PlanRequestStatus, PlanBillingPeriod

        # Create active plan for student
        active_req = PlanRequest.objects.create(
            user=self.student,
            plan=self.plan,
            periodo=PlanBillingPeriod.QUARTERLY,
            metodo_pago=PaymentMethod.IN_STUDIO,
            estado=PlanRequestStatus.CONFIRMED,
        )

        res = self.client.get(reverse("core:student_dashboard"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["selected_plan"], self.plan)
        self.assertEqual(res.context["selected_period"], PlanBillingPeriod.QUARTERLY)




