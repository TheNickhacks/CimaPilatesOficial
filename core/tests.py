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

