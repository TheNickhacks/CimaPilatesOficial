from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.signing import TimestampSigner
from django.urls import reverse
from django.utils import timezone

from core.emails import send_class_reservation_confirmation_request_email
from core.models import ClassReservation
from core.views import _booking_window_allows_session, _format_session_label, _get_booking_close_delta, _get_session_local_datetime


class Command(BaseCommand):
	help = "Envía correos para reconfirmar reservas según la ventana (AM: 10h, resto: 3h)."

	def add_arguments(self, parser):
		parser.add_argument(
			"--days",
			type=int,
			default=2,
			help="Cantidad de días hacia adelante a revisar (por defecto: 2).",
		)

	def handle(self, *args, **options):
		now = timezone.now()
		window_end = now + timedelta(days=max(int(options.get("days") or 2), 1))
		signer = TimestampSigner(salt="class-reservation-confirm")

		reservations = list(
			ClassReservation.objects.select_related("class_session", "user")
			.filter(
				confirmation_requested_at__isnull=True,
				class_session__starts_at__gte=now,
				class_session__starts_at__lt=window_end,
			)
			.order_by("class_session__starts_at")
		)

		sent = 0
		skipped = 0
		failed = 0
		for reservation in reservations:
			class_session = reservation.class_session
			local_start = _get_session_local_datetime(class_session.starts_at)
			close_delta = _get_booking_close_delta(class_session)
			local_now = timezone.localtime(now)
			if not (local_start - close_delta <= local_now < local_start):
				skipped += 1
				continue

			allowed, _ = _booking_window_allows_session(class_session, now=now)
			if allowed:
				skipped += 1
				continue

			to_email = getattr(reservation.user, "email", "") or ""
			if not to_email:
				skipped += 1
				continue

			token = signer.sign(str(reservation.id))
			confirm_url = f"{settings.SITE_URL}{reverse('core:confirm_class_reservation', args=[token])}"
			full_name = reservation.user.get_full_name() or to_email
			try:
				send_class_reservation_confirmation_request_email(
					to_email,
					full_name,
					_format_session_label(class_session),
					confirm_url,
					fail_silently=False,
				)
				reservation.confirmation_requested_at = now
				reservation.save(update_fields=["confirmation_requested_at"])
				sent += 1
			except Exception:
				failed += 1
				self.stderr.write(f"FAILED|{reservation.id}")

		self.stdout.write(f"SENT|{sent}")
		self.stdout.write(f"SKIPPED|{skipped}")
		self.stdout.write(f"FAILED|{failed}")
