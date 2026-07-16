from calendar import monthrange
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone as dt_timezone

from django.contrib import messages
from django.db import IntegrityError, models, transaction
from django.contrib.auth.decorators import login_required
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import User, UserRole
from accounts.permissions import admin_required, student_required, teacher_required
from . import holidays_cl
from .emails import send_plan_request_received_email, send_single_class_request_received_email
from .forms import ClassReservationForm, LandingLeadForm, PlanRequestForm, SingleClassPublicBookingForm
from .models import (
	ClassCreditAdjustment,
	ClassAttendance,
	ClassReservation,
	ClassSession,
	AdminActionLog,
	AdminActionType,
	PlanBillingPeriod,
	PlanCatalog,
	PlanRequest,
	PlanRequestStatus,
	SingleClassBooking,
	SingleClassBookingStatus,
	TeacherHoursAdjustment,
	TeacherSessionNote,
	TeacherShiftKind,
	TeacherMonthlyShift,
	TeacherWorkShift,
)


TRANSFER_DETAILS = (
	("Nombre", "Cima.Pilates SpA"),
	("RUT", "78434624-2"),
	("Banco", "Scotiabank Chile / Sudamericano"),
	("Tipo de cuenta", "Corriente"),
	("Numero de cuenta", "994170058"),
	("Correo", "nnavarrogarrido02@gmail.com"),
)

DISPLAY_SCHEDULE_DAYS = 21
TEACHER_DASHBOARD_DAYS = 21
BOOKING_OPEN_DELTA = timedelta(days=7)
DEFAULT_CLASS_CAPACITY = 4
WEEKDAYS_ES_LIST = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

def _get_spanish_weekday(date_obj):
	return WEEKDAYS_ES_LIST[date_obj.weekday()]

def _get_spanish_date_label(date_obj):
	return f"{_get_spanish_weekday(date_obj)} {date_obj.strftime('%d/%m/%Y')}"

def _get_calendar_navigation_start_date(today):
	current_monday = today - timedelta(days=today.weekday())
	if today.weekday() >= 5: # Sábado o Domingo
		return current_monday + timedelta(days=7)
	return current_monday

STUDIO_SLOT_TIMES = {
	0: (
		(time(7, 10), time(8, 0)),
		(time(8, 10), time(9, 0)),
		(time(9, 10), time(10, 0)),
		(time(10, 10), time(11, 0)),
		(time(11, 10), time(12, 0)),
		(time(16, 10), time(17, 0)),
		(time(17, 10), time(18, 0)),
		(time(18, 10), time(19, 0)),
		(time(19, 10), time(20, 0)),
		(time(20, 10), time(21, 0)),
	),
	1: (
		(time(7, 10), time(8, 0)),
		(time(8, 10), time(9, 0)),
		(time(9, 10), time(10, 0)),
		(time(10, 10), time(11, 0)),
		(time(11, 10), time(12, 0)),
		(time(16, 10), time(17, 0)),
		(time(17, 10), time(18, 0)),
		(time(18, 10), time(19, 0)),
		(time(19, 10), time(20, 0)),
		(time(20, 10), time(21, 0)),
	),
	2: (
		(time(7, 10), time(8, 0)),
		(time(8, 10), time(9, 0)),
		(time(9, 10), time(10, 0)),
		(time(10, 10), time(11, 0)),
		(time(11, 10), time(12, 0)),
		(time(16, 10), time(17, 0)),
		(time(17, 10), time(18, 0)),
		(time(18, 10), time(19, 0)),
		(time(19, 10), time(20, 0)),
		(time(20, 10), time(21, 0)),
	),
	3: (
		(time(7, 10), time(8, 0)),
		(time(8, 10), time(9, 0)),
		(time(9, 10), time(10, 0)),
		(time(10, 10), time(11, 0)),
		(time(11, 10), time(12, 0)),
		(time(16, 10), time(17, 0)),
		(time(17, 10), time(18, 0)),
		(time(18, 10), time(19, 0)),
		(time(19, 10), time(20, 0)),
		(time(20, 10), time(21, 0)),
	),
	4: (
		(time(7, 10), time(8, 0)),
		(time(8, 10), time(9, 0)),
		(time(9, 10), time(10, 0)),
		(time(10, 10), time(11, 0)),
		(time(11, 10), time(12, 0)),
		(time(16, 10), time(17, 0)),
		(time(17, 10), time(18, 0)),
		(time(18, 10), time(19, 0)),
		(time(19, 10), time(20, 0)),
		(time(20, 10), time(21, 0)),
	),
	5: (
		(time(9, 10), time(10, 0)),
		(time(10, 10), time(11, 0)),
		(time(11, 10), time(12, 0)),
		(time(12, 10), time(13, 0)),
		(time(13, 10), time(14, 0)),
	),
}
ACTIVE_SINGLE_CLASS_STATUSES = (
	SingleClassBookingStatus.PENDING,
	SingleClassBookingStatus.CONFIRMED,
)


def _ensure_aware_datetime(value):
	if timezone.is_naive(value):
		return timezone.make_aware(value, timezone.get_current_timezone())
	return value


def _get_safe_local_datetime(value):
	if value is None:
		return None
	if timezone.is_naive(value):
		return timezone.localtime(value.replace(tzinfo=dt_timezone.utc), timezone.get_current_timezone())
	return timezone.localtime(value, timezone.get_current_timezone())


def _get_session_local_datetime(value):
	if timezone.is_naive(value):
		return timezone.localtime(value.replace(tzinfo=dt_timezone.utc), timezone.get_current_timezone())
	return timezone.localtime(value, timezone.get_current_timezone())


def _to_session_storage_datetime(value):
	local_value = value
	if timezone.is_naive(local_value):
		local_value = timezone.make_aware(local_value, timezone.get_current_timezone())
	return local_value.astimezone(dt_timezone.utc)


def _normalize_session_storage_datetime(value):
	if timezone.is_naive(value):
		return value.replace(tzinfo=dt_timezone.utc)
	return value.astimezone(dt_timezone.utc)


def _combine_local_datetime(day, value):
	return timezone.make_aware(datetime.combine(day, value), timezone.get_current_timezone())


def _add_months(value, months):
	month_index = value.month - 1 + months
	year = value.year + month_index // 12
	month = month_index % 12 + 1
	day = min(value.day, monthrange(year, month)[1])
	return value.replace(year=year, month=month, day=day)


def _get_plan_valid_until(plan_request):
	months_by_period = {
		PlanBillingPeriod.MONTHLY: 1,
		PlanBillingPeriod.QUARTERLY: 3,
		PlanBillingPeriod.SEMESTER: 6,
	}
	created_at = _ensure_aware_datetime(plan_request.created_at)
	return _add_months(created_at, months_by_period.get(plan_request.periodo, 1))


def _get_plan_total_class_limit(plan_request):
	months_by_period = {
		PlanBillingPeriod.MONTHLY: 1,
		PlanBillingPeriod.QUARTERLY: 3,
		PlanBillingPeriod.SEMESTER: 6,
	}
	months = months_by_period.get(plan_request.periodo, 1)
	return int(plan_request.plan.clases_por_mes) * int(months)


def _get_plan_bonus_class_count(user, plan_request):
	total = (
		ClassCreditAdjustment.objects.filter(user=user, plan_request=plan_request)
		.aggregate(models.Sum("cantidad"))
		.get("cantidad__sum")
	)
	return int(total or 0)


def _get_plan_used_class_count(user, plan_request, now=None):
	now = now or timezone.now()
	valid_until = _get_plan_valid_until(plan_request)
	if valid_until <= now:
		return 0
	window_start = _to_session_storage_datetime(_ensure_aware_datetime(plan_request.created_at))
	window_end = _to_session_storage_datetime(_ensure_aware_datetime(valid_until))
	return int(
		ClassReservation.objects.filter(
			user=user,
			class_session__starts_at__gte=window_start,
			class_session__starts_at__lt=window_end,
		).count()
	)


def _format_remaining_time(valid_until):
	remaining = _ensure_aware_datetime(valid_until) - timezone.now()
	if remaining.total_seconds() <= 0:
		return "Vigencia finalizada", True

	days = remaining.days
	hours = remaining.seconds // 3600
	if days > 0 and hours > 0:
		return f"{days} dias y {hours} horas restantes", False
	if days > 0:
		return f"{days} dias restantes", False
	if hours > 0:
		return f"{hours} horas restantes", False
	minutes = max(remaining.seconds // 60, 1)
	return f"{minutes} minutos restantes", False


def _get_active_plan_request(user):
	return (
		PlanRequest.objects.filter(user=user, estado=PlanRequestStatus.CONFIRMED)
		.select_related("plan")
		.first()
	)


def _get_week_bounds_from_datetime(value):
	local_value = _get_session_local_datetime(value)
	week_start_date = local_value.date() - timedelta(days=local_value.weekday())
	week_start = _combine_local_datetime(week_start_date, time(0, 0))
	week_end = week_start + timedelta(days=7)
	return week_start, week_end


def _generate_day_slots(day):
	if holidays_cl.is_holiday(day) or day.weekday() == 6:
		return
	for start_time, end_time in STUDIO_SLOT_TIMES.get(day.weekday(), ()):
		yield _combine_local_datetime(day, start_time), _combine_local_datetime(day, end_time)


def _get_teacher_display_for_session(class_session, teachers=None, monthly_shifts=None):
	local_start = _get_session_local_datetime(class_session.starts_at)
	shift_kind = _get_shift_kind_for_local_start(local_start)
	if shift_kind is None:
		return "Profesora por confirmar"

	if monthly_shifts is not None:
		matching_shifts = [
			s for s in monthly_shifts
			if s.year == local_start.year and s.month == local_start.month and s.shift_kind == shift_kind
		]
		# If the pre-fetched objects do not have select_related teacher, we can resolve from teachers list
		# but normally they have it. Let's make it robust:
		if matching_shifts and teachers is not None:
			teacher_ids = {s.teacher_id for s in matching_shifts}
			matching_teachers = [t for t in teachers if t.id in teacher_ids]
			if matching_teachers:
				return ", ".join(t.get_full_name() or t.email for t in matching_teachers)
	else:
		matching_shifts = list(
			TeacherMonthlyShift.objects.filter(
				year=local_start.year,
				month=local_start.month,
				shift_kind=shift_kind
			).select_related("teacher")
		)

	if not matching_shifts:
		return "Profesora por confirmar"

	return ", ".join((s.teacher.get_full_name() or s.teacher.email) for s in matching_shifts)


def _get_shift_kind_for_local_start(local_start):
	if local_start.weekday() == 5:
		return TeacherShiftKind.SATURDAY
	if local_start.weekday() > 5:
		return None
	if local_start.time() < time(12, 0):
		return TeacherShiftKind.AM
	if local_start.time() >= time(16, 0):
		return TeacherShiftKind.PM
	return None


def _get_shift_time_range_label(shift_kind):
	if shift_kind == TeacherShiftKind.AM:
		return "07:10 - 12:00"
	if shift_kind == TeacherShiftKind.PM:
		return "16:10 - 21:00"
	return "09:10 - 14:00"


def _validate_teacher_shift(shift_date, shift_kind):
	if shift_date < timezone.localdate():
		return False, "Solo puedes asignar turnos desde hoy en adelante."
	if shift_date.weekday() == 6:
		return False, "Los domingos no tienen clases programadas."
	if shift_date.weekday() == 5 and shift_kind != TeacherShiftKind.SATURDAY:
		return False, "Los sábados solo admiten el turno Sábado de 09:10 a 14:00."
	if shift_date.weekday() < 5 and shift_kind == TeacherShiftKind.SATURDAY:
		return False, "El turno Sábado solo puede usarse en días sábado."
	if shift_date.weekday() < 5 and shift_kind not in {TeacherShiftKind.AM, TeacherShiftKind.PM}:
		return False, "Selecciona un bloque válido para el día elegido."
	return True, ""


def _get_teacher_month_key_from_session(class_session):
	local_start = _get_session_local_datetime(class_session.starts_at)
	shift_kind = _get_shift_kind_for_local_start(local_start)
	if shift_kind is None:
		return None
	return (local_start.year, local_start.month, shift_kind)


def _get_teacher_monthly_shift_set(teacher, year_month_pairs=None):
	query = TeacherMonthlyShift.objects.filter(teacher=teacher)
	if year_month_pairs:
		q = models.Q()
		for year, month in year_month_pairs:
			q |= models.Q(year=year, month=month)
		query = query.filter(q)
	return {(item.year, item.month, item.shift_kind) for item in query}


def _teacher_has_access_to_session(teacher, class_session, monthly_shift_set=None):
	shift_key = _get_teacher_month_key_from_session(class_session)
	if shift_key is None:
		return False
	if monthly_shift_set is None:
		monthly_shift_set = _get_teacher_monthly_shift_set(teacher)
	return shift_key in monthly_shift_set


def _format_minutes_label(total_minutes):
	hours, minutes = divmod(max(int(total_minutes), 0), 60)
	if hours and minutes:
		return f"{hours} h {minutes} min"
	if hours:
		return f"{hours} h"
	return f"{minutes} min"


def _get_counted_session_minutes(local_start, local_end):
	if local_start.time() == time(7, 10) and local_end.time() == time(8, 0):
		return 60
	return int((local_end - local_start).total_seconds() // 60)


def _build_teacher_month_metrics(teacher, target_month=None, prefetch_data=None):
	target_month = target_month or timezone.localdate()
	month_start = target_month.replace(day=1)
	next_month = _add_months(_combine_local_datetime(month_start, time(0, 0)), 1).date()
	month_end = next_month - timedelta(days=1)
	today = timezone.localdate()
	if (month_start.year, month_start.month) == (today.year, today.month):
		cutoff_date = today
	elif month_start < today.replace(day=1):
		cutoff_date = month_end
	else:
		cutoff_date = month_start - timedelta(days=1)

	if prefetch_data is not None:
		selected_shift_kinds = prefetch_data["shifts"].get(teacher.id, set())
	else:
		selected_shift_kinds = set(
			TeacherMonthlyShift.objects.filter(
				teacher=teacher,
				year=month_start.year,
				month=month_start.month,
			).values_list("shift_kind", flat=True)
		)
	monthly_shift_set = {(month_start.year, month_start.month, kind) for kind in selected_shift_kinds}

	scheduled_shift_day_count = 0
	current_day = month_start
	loop_end = month_end
	while current_day <= loop_end:
		if current_day.weekday() == 6:
			current_day += timedelta(days=1)
			continue
		if current_day.weekday() == 5:
			if TeacherShiftKind.SATURDAY in selected_shift_kinds:
				scheduled_shift_day_count += 1
		else:
			if TeacherShiftKind.AM in selected_shift_kinds or TeacherShiftKind.PM in selected_shift_kinds:
				scheduled_shift_day_count += 1
		current_day += timedelta(days=1)

	window_start = _to_session_storage_datetime(_combine_local_datetime(month_start, time(0, 0)))
	window_end = _to_session_storage_datetime(_combine_local_datetime(next_month, time(0, 0)))
	
	month_sessions = []
	if prefetch_data is not None:
		sessions_pool = prefetch_data["sessions"]
	else:
		sessions_pool = list(ClassSession.objects.filter(starts_at__gte=window_start, starts_at__lt=window_end).order_by("starts_at"))

	for session in sessions_pool:
		if not _teacher_has_access_to_session(teacher, session, monthly_shift_set=monthly_shift_set):
			continue
		local_start = _get_session_local_datetime(session.starts_at)
		if local_start.date() > cutoff_date:
			continue
		month_sessions.append(session)

	if prefetch_data is not None:
		session_ids_set = {s.id for s in month_sessions}
		student_reservations = [r for r in prefetch_data["reservations"] if r.class_session_id in session_ids_set]
		single_class_requests = [b for b in prefetch_data["single_bookings"] if b.class_session_id in session_ids_set]
		
		student_by_session = defaultdict(list)
		single_class_by_session = defaultdict(list)
		for reservation in student_reservations:
			student_by_session[reservation.class_session_id].append(reservation)
		for booking in single_class_requests:
			single_class_by_session[booking.class_session_id].append(booking)
		total_by_session = defaultdict(int)
		for session in month_sessions:
			total_by_session[session.id] = len(student_by_session[session.id]) + len(single_class_by_session[session.id])
		
		capacity_maps = {
			"student_reservations": student_reservations,
			"student_by_session": student_by_session,
			"single_class_requests": single_class_requests,
			"single_class_by_session": single_class_by_session,
			"total_by_session": total_by_session,
		}
	else:
		capacity_maps = _get_capacity_maps(month_sessions)
		student_reservations = capacity_maps["student_reservations"]

	if prefetch_data is not None:
		present_session_ids = {a.class_session_id for a in prefetch_data["attendances"] if a.present and a.class_session_id in session_ids_set}
		total_effective_minutes, last_block_skipped_count = _count_teacher_effective_minutes(month_sessions, present_session_ids=present_session_ids)
	else:
		total_effective_minutes, last_block_skipped_count = _count_teacher_effective_minutes(month_sessions)

	if prefetch_data is not None:
		adjustment_minutes = prefetch_data["adjustments"].get(teacher.id, 0)
	else:
		adjustment_minutes = int(
			TeacherHoursAdjustment.objects.filter(
				teacher=teacher,
				year=month_start.year,
				month=month_start.month,
			).aggregate(models.Sum("minutes_delta")).get("minutes_delta__sum")
			or 0
		)
	total_effective_minutes += adjustment_minutes

	if prefetch_data is not None:
		attendance_marked_count = sum(1 for a in prefetch_data["attendances"] if a.teacher_id == teacher.id and a.class_session_id in session_ids_set and a.present)
	else:
		attendance_marked_count = ClassAttendance.objects.filter(
			teacher=teacher,
			class_session__in=month_sessions,
			present=True,
		).count()

	unique_student_ids = {reservation.user_id for reservation in student_reservations}
	return {
		"month_label": month_start.strftime("%B %Y").capitalize(),
		"selected_shift_kind_count": len(selected_shift_kinds),
		"scheduled_shift_day_count": scheduled_shift_day_count,
		"accessible_session_count": len(month_sessions),
		"classes_with_students_count": sum(
			1 for session in month_sessions if capacity_maps["total_by_session"][session.id] > 0
		),
		"effective_minutes": total_effective_minutes,
		"effective_hours_label": _format_minutes_label(total_effective_minutes),
		"effective_cutoff_label": cutoff_date.strftime("%d/%m/%Y") if cutoff_date >= month_start else month_start.strftime("%d/%m/%Y"),
		"adjustment_minutes": adjustment_minutes,
		"adjustment_label": _format_minutes_label(abs(adjustment_minutes)) if adjustment_minutes else "",
		"last_block_skipped_count": last_block_skipped_count,
		"attendance_marked_count": attendance_marked_count,
		"unique_students_count": len(unique_student_ids),
	}


def _build_teacher_schedule_context(teacher, selected_session_id=None, selected_month=None):
	today = timezone.localdate()
	_ensure_schedule_sessions(today, TEACHER_DASHBOARD_DAYS)
	window_start = _to_session_storage_datetime(_combine_local_datetime(today, time(0, 0)))
	window_end = _to_session_storage_datetime(
		_combine_local_datetime(today + timedelta(days=TEACHER_DASHBOARD_DAYS), time(0, 0))
	)
	selected_month = selected_month or today.replace(day=1)
	selected_month_start = selected_month.replace(day=1)
	selected_month_str = f"{selected_month_start.year}-{selected_month_start.month:02d}"
	selected_month_shift_kinds = list(
		TeacherMonthlyShift.objects.filter(
			teacher=teacher,
			year=selected_month_start.year,
			month=selected_month_start.month,
		).values_list("shift_kind", flat=True)
	)

	end_date = today + timedelta(days=TEACHER_DASHBOARD_DAYS)
	year_month_pairs = []
	month_cursor = today.replace(day=1)
	last_month = end_date.replace(day=1)
	while month_cursor <= last_month:
		year_month_pairs.append((month_cursor.year, month_cursor.month))
		month_cursor = _add_months(_combine_local_datetime(month_cursor, time(0, 0)), 1).date()
	monthly_shift_set = _get_teacher_monthly_shift_set(teacher, year_month_pairs=year_month_pairs)
	sessions = [
		session
		for session in ClassSession.objects.filter(starts_at__gte=window_start, starts_at__lt=window_end).order_by("starts_at")
		if _teacher_has_access_to_session(teacher, session, monthly_shift_set=monthly_shift_set)
	]
	capacity_maps = _get_capacity_maps(sessions)
	attendance_records = list(
		ClassAttendance.objects.filter(class_session__in=sessions).select_related("user", "teacher")
	)
	attendance_by_session_user = {
		(record.class_session_id, record.user_id): record
		for record in attendance_records
	}
	notes_by_session = {
		note.class_session_id: note
		for note in TeacherSessionNote.objects.filter(class_session__in=sessions, teacher=teacher)
	}
	schedule_days = []
	for session in sessions:
		local_start = _get_session_local_datetime(session.starts_at)
		local_end = _get_session_local_datetime(session.ends_at)
		if not _is_valid_schedule_slot(local_start, local_end):
			continue
		day_key = local_start.date()
		if not schedule_days or schedule_days[-1]["date"] != day_key:
			schedule_days.append(
				{
					"date": day_key,
					"weekday": _get_spanish_weekday(local_start),
					"slots": [],
				}
			)
		student_reservations = capacity_maps["student_by_session"][session.id]
		present_count = sum(
			1
			for reservation in student_reservations
			if attendance_by_session_user.get((session.id, reservation.user_id))
			and attendance_by_session_user[(session.id, reservation.user_id)].present
		)
		schedule_days[-1]["slots"].append(
			{
				"session": session,
				"date_label": _get_spanish_date_label(local_start),
				"time_label": f"{local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}",
				"time_key": local_start.strftime("%H:%M"),
				"date": day_key,
				"starts_at_local": local_start,
				"ends_at_local": local_end,
				"student_count": len(student_reservations),
				"single_class_count": len(capacity_maps["single_class_by_session"][session.id]),
				"total_count": capacity_maps["total_by_session"][session.id],
				"attendance_present_count": present_count,
				"capacity_left": max(session.capacidad_maxima - capacity_maps["total_by_session"][session.id], 0),
				"is_selected": selected_session_id == session.id,
				"teacher_note_preview": (notes_by_session.get(session.id).note[:80] if notes_by_session.get(session.id) else ""),
			}
		)

	calendar_weeks = _build_calendar_weeks(schedule_days)
	selected_session = next((session for session in sessions if session.id == selected_session_id), None)
	if selected_session is None and sessions:
		selected_session = sessions[0]
	selected_attendance = []
	selected_note = None
	selected_stats = {}
	if selected_session is not None:
		selected_note = notes_by_session.get(selected_session.id)
		selected_reservations = capacity_maps["student_by_session"][selected_session.id]
		selected_user_ids = [reservation.user_id for reservation in selected_reservations]
		user_attendance_totals = defaultdict(lambda: {"present": 0, "records": 0})
		for record in ClassAttendance.objects.filter(user_id__in=selected_user_ids):
			user_attendance_totals[record.user_id]["records"] += 1
			if record.present:
				user_attendance_totals[record.user_id]["present"] += 1
		selected_stats = {
			"student_count": len(selected_reservations),
			"single_class_count": len(capacity_maps["single_class_by_session"][selected_session.id]),
			"capacity_left": max(
				selected_session.capacidad_maxima - capacity_maps["total_by_session"][selected_session.id],
				0,
			),
			"total_count": capacity_maps["total_by_session"][selected_session.id],
		}
		for reservation in selected_reservations:
			attendance_record = attendance_by_session_user.get((selected_session.id, reservation.user_id))
			attendance_totals = user_attendance_totals[reservation.user_id]
			selected_attendance.append(
				{
					"reservation": reservation,
					"user": reservation.user,
					"is_present": attendance_record.present if attendance_record is not None else False,
					"marked_at": _get_safe_local_datetime(attendance_record.marked_at).strftime("%d/%m/%Y %H:%M")
					if attendance_record is not None and _get_safe_local_datetime(attendance_record.marked_at) is not None
					else "",
					"attendance_present_total": attendance_totals["present"],
					"attendance_record_total": attendance_totals["records"],
				}
			)

	return {
		"teacher_selected_month": selected_month_str,
		"teacher_selected_month_label": selected_month_start.strftime("%B %Y").capitalize(),
		"teacher_selected_shift_kinds": selected_month_shift_kinds,
		"calendar_weeks": calendar_weeks,
		"default_calendar_week_index": _get_default_calendar_week_index(
			calendar_weeks,
			preferred_session_id=selected_session.id if selected_session else None,
		),
		"selected_teacher_session": selected_session,
		"selected_teacher_session_local_start": _get_session_local_datetime(selected_session.starts_at) if selected_session else None,
		"selected_teacher_session_local_end": _get_session_local_datetime(selected_session.ends_at) if selected_session else None,
		"selected_teacher_session_students": selected_attendance,
		"selected_teacher_session_single_bookings": capacity_maps["single_class_by_session"][selected_session.id] if selected_session else [],
		"selected_teacher_note": selected_note.note if selected_note else "",
		"selected_teacher_stats": selected_stats,
		"teacher_month_metrics": _build_teacher_month_metrics(teacher, target_month=selected_month_start),
		"teacher_shift_choices": TeacherShiftKind.choices,
	}


def _is_valid_schedule_slot(starts_at_local, ends_at_local):
	for expected_start, expected_end in _generate_day_slots(starts_at_local.date()):
		if starts_at_local == expected_start and ends_at_local == expected_end:
			return True
	return False


def _ensure_schedule_sessions(start_date, total_days):
	cache_key = f"ensure_sessions_{start_date}_{total_days}_v6"
	if cache.get(cache_key):
		return

	expected_sessions = {}
	for day_offset in range(total_days):
		target_date = start_date + timedelta(days=day_offset)
		for starts_at, ends_at in _generate_day_slots(target_date):
			storage_start = _to_session_storage_datetime(starts_at)
			expected_sessions[storage_start] = {
				"ends_at": _to_session_storage_datetime(ends_at),
				"capacidad_maxima": DEFAULT_CLASS_CAPACITY,
			}

	if not expected_sessions:
		return

	window_start = min(expected_sessions.keys())
	window_end = max(expected_sessions.keys()) + timedelta(seconds=1)

	# Update existing sessions to match the new times in place, preserving DB data and IDs
	for session in ClassSession.objects.filter(starts_at__gte=window_start, starts_at__lt=window_end):
		local_start = _get_session_local_datetime(session.starts_at)
		t = local_start.time()
		day = local_start.date()
		new_start_local = None
		new_end_local = None
		if local_start.weekday() < 5:  # Weekday
			if t == time(8, 0):
				new_start_local = _combine_local_datetime(day, time(8, 10))
				new_end_local = _combine_local_datetime(day, time(9, 0))
			elif t == time(9, 0):
				new_start_local = _combine_local_datetime(day, time(9, 10))
				new_end_local = _combine_local_datetime(day, time(10, 0))
			elif t == time(10, 0):
				new_start_local = _combine_local_datetime(day, time(10, 10))
				new_end_local = _combine_local_datetime(day, time(11, 0))
			elif t == time(11, 0):
				new_start_local = _combine_local_datetime(day, time(11, 10))
				new_end_local = _combine_local_datetime(day, time(12, 0))
			elif t == time(16, 0):
				new_start_local = _combine_local_datetime(day, time(16, 10))
				new_end_local = _combine_local_datetime(day, time(17, 0))
			elif t == time(17, 0):
				new_start_local = _combine_local_datetime(day, time(17, 10))
				new_end_local = _combine_local_datetime(day, time(18, 0))
			elif t == time(18, 0):
				new_start_local = _combine_local_datetime(day, time(18, 10))
				new_end_local = _combine_local_datetime(day, time(19, 0))
			elif t == time(19, 0):
				new_start_local = _combine_local_datetime(day, time(19, 10))
				new_end_local = _combine_local_datetime(day, time(20, 0))
			elif t == time(20, 0):
				new_start_local = _combine_local_datetime(day, time(20, 10))
				new_end_local = _combine_local_datetime(day, time(21, 0))
		elif local_start.weekday() == 5:  # Saturday
			if t in {time(9, 0), time(9, 10)}:
				if t != time(9, 10) or session.ends_at.time() != time(10, 0):
					new_start_local = _combine_local_datetime(day, time(9, 10))
					new_end_local = _combine_local_datetime(day, time(10, 0))
			elif t in {time(10, 0), time(10, 10)}:
				if t != time(10, 10) or session.ends_at.time() != time(11, 0):
					new_start_local = _combine_local_datetime(day, time(10, 10))
					new_end_local = _combine_local_datetime(day, time(11, 0))
			elif t in {time(11, 0), time(11, 10)}:
				if t != time(11, 10) or session.ends_at.time() != time(12, 0):
					new_start_local = _combine_local_datetime(day, time(11, 10))
					new_end_local = _combine_local_datetime(day, time(12, 0))
			elif t in {time(12, 0), time(12, 10)}:
				if t != time(12, 10) or session.ends_at.time() != time(13, 0):
					new_start_local = _combine_local_datetime(day, time(12, 10))
					new_end_local = _combine_local_datetime(day, time(13, 0))
			elif t in {time(13, 0), time(13, 10)}:
				if t != time(13, 10) or session.ends_at.time() != time(14, 0):
					new_start_local = _combine_local_datetime(day, time(13, 10))
					new_end_local = _combine_local_datetime(day, time(14, 0))

		if new_start_local and new_end_local:
			session.starts_at = _to_session_storage_datetime(new_start_local)
			session.ends_at = _to_session_storage_datetime(new_end_local)
			try:
				session.save(update_fields=["starts_at", "ends_at", "updated_at"])
			except Exception:
				pass

	existing_sessions = {
		_normalize_session_storage_datetime(session.starts_at): session
		for session in ClassSession.objects.filter(starts_at__gte=window_start, starts_at__lt=window_end)
	}

	sessions_to_create = []
	sessions_to_update = []
	for storage_start, session_data in expected_sessions.items():
		existing_session = existing_sessions.get(storage_start)
		if existing_session is None:
			sessions_to_create.append(
				ClassSession(
					starts_at=storage_start,
					ends_at=session_data["ends_at"],
					capacidad_maxima=session_data["capacidad_maxima"],
				)
			)
			continue

		expected_end = session_data["ends_at"]
		normalized_end = _normalize_session_storage_datetime(existing_session.ends_at)
		if normalized_end != expected_end or existing_session.capacidad_maxima != session_data["capacidad_maxima"]:
			existing_session.ends_at = expected_end
			existing_session.capacidad_maxima = session_data["capacidad_maxima"]
			sessions_to_update.append(existing_session)

	if sessions_to_create:
		ClassSession.objects.bulk_create(sessions_to_create, ignore_conflicts=True)
	if sessions_to_update:
		ClassSession.objects.bulk_update(sessions_to_update, ["ends_at", "capacidad_maxima"])

	cache.set(cache_key, True, 3600)  # cache for 1 hour


def _get_booking_close_delta(class_session):
	starts_at_local = _get_session_local_datetime(class_session.starts_at)
	if starts_at_local.time() < time(10, 0):
		return timedelta(hours=10)
	return timedelta(hours=3)


def _booking_window_allows_session(class_session, now=None):
	now = now or timezone.now()
	starts_at = _get_session_local_datetime(class_session.starts_at)
	if getattr(class_session, "is_blocked", False):
		return False, class_session.blocked_reason or "Este bloque fue bloqueado por administración."
	if starts_at.weekday() == 6:
		return False, "No hay clases disponibles los domingos."
	holiday_name = holidays_cl.get_holiday_name(starts_at.date())
	if holiday_name:
		return False, f"No hay clases disponibles por feriado: {holiday_name}."
	if now < starts_at - BOOKING_OPEN_DELTA:
		return False, "Esta clase se habilita exactamente una semana antes de su inicio."
	if starts_at <= now:
		return False, "Este bloque ya comenzo o ya paso."
	close_delta = _get_booking_close_delta(class_session)
	if now >= starts_at - close_delta:
		closes_at_label = (starts_at - close_delta).strftime("%d/%m/%Y %H:%M")
		return (
			False,
			f"Las reservas para este bloque cierran {int(close_delta.total_seconds() // 3600)} horas antes del inicio (cierre: {closes_at_label}).",
		)
	return True, ""


def _plan_allows_booking(plan_request, class_session, now=None):
	now = now or timezone.now()
	window_allowed, window_message = _booking_window_allows_session(class_session, now=now)
	if not window_allowed:
		return False, window_message
	if plan_request is None:
		return False, "Necesitas un plan activo para reservar clases."
	valid_until = _get_plan_valid_until(plan_request)
	if valid_until <= now:
		return False, "Tu plan ya no tiene vigencia activa."
	if _get_session_local_datetime(class_session.starts_at) > valid_until:
		return False, "La fecha de esta clase supera la vigencia de tu plan actual."
	allowed_total = _get_plan_total_class_limit(plan_request) + _get_plan_bonus_class_count(plan_request.user, plan_request)
	used_total = _get_plan_used_class_count(plan_request.user, plan_request, now=now)
	if used_total >= allowed_total:
		return False, "Ya alcanzaste el maximo total de clases disponibles para tu plan vigente."
	return True, ""


def _build_calendar_weeks(schedule_days):
	if not schedule_days:
		return []

	day_lookup = {day["date"]: day for day in schedule_days}
	first_day = schedule_days[0]["date"]
	last_day = schedule_days[-1]["date"]
	first_week_start = first_day - timedelta(days=first_day.weekday())
	last_week_start = last_day - timedelta(days=last_day.weekday())

	calendar_weeks = []
	week_start = first_week_start
	while week_start <= last_week_start:
		week_days = []
		time_keys = set()
		for day_offset in range(7):
			current_date = week_start + timedelta(days=day_offset)
			holiday_name = holidays_cl.get_holiday_name(current_date)
			day_data = day_lookup.get(
				current_date,
				{
					"date": current_date,
					"weekday": _get_spanish_weekday(current_date),
					"slots": [],
				},
			)
			slot_map = {}
			for slot in day_data["slots"]:
				time_key = slot["time_key"]
				slot_map[time_key] = slot
				time_keys.add(time_key)
			week_days.append(
				{
					"date": current_date,
					"weekday": day_data["weekday"],
					"slots": day_data["slots"],
					"slot_map": slot_map,
					"is_holiday": holiday_name is not None,
					"holiday_name": holiday_name or "",
					"is_closed": bool(holiday_name) or not day_data["slots"],
				}
			)

		time_rows = []
		for time_key in sorted(time_keys):
			time_rows.append(
				{
					"time_key": time_key,
					"cells": [day["slot_map"].get(time_key) for day in week_days],
				}
			)

		calendar_weeks.append(
			{
				"label": f"{week_start.strftime('%d/%m')} - {(week_start + timedelta(days=6)).strftime('%d/%m')}",
				"days": week_days,
				"time_rows": time_rows,
			}
		)
		week_start += timedelta(days=7)

	return calendar_weeks


def _get_default_calendar_week_index(calendar_weeks, preferred_session_id=None):
	if not calendar_weeks:
		return 0

	if preferred_session_id is not None:
		for index, week in enumerate(calendar_weeks):
			for row in week["time_rows"]:
				for slot in row["cells"]:
					if slot and slot["session"].id == preferred_session_id:
						return index

	for index, week in enumerate(calendar_weeks):
		if any(row["time_key"] == "07:10" for row in week["time_rows"]):
			return index

	best_index = 0
	best_score = -1
	for index, week in enumerate(calendar_weeks):
		score = sum(1 for row in week["time_rows"] for slot in row["cells"] if slot)
		if score > best_score:
			best_index = index
			best_score = score
	return best_index


def _get_capacity_maps(sessions):
	student_reservations = list(
		ClassReservation.objects.filter(class_session__in=sessions).select_related("user")
	)
	single_class_requests = list(
		SingleClassBooking.objects.filter(
			class_session__in=sessions,
			estado__in=ACTIVE_SINGLE_CLASS_STATUSES,
		)
	)
	student_by_session = defaultdict(list)
	single_class_by_session = defaultdict(list)
	for reservation in student_reservations:
		student_by_session[reservation.class_session_id].append(reservation)
	for booking in single_class_requests:
		single_class_by_session[booking.class_session_id].append(booking)
	total_by_session = defaultdict(int)
	for session in sessions:
		total_by_session[session.id] = len(student_by_session[session.id]) + len(single_class_by_session[session.id])
	return {
		"student_reservations": student_reservations,
		"student_by_session": student_by_session,
		"single_class_requests": single_class_requests,
		"single_class_by_session": single_class_by_session,
		"total_by_session": total_by_session,
	}


def _build_plan_request_kind(user, plan):
	active_plan_request = _get_active_plan_request(user)
	if active_plan_request is None:
		return "new_plan"
	if active_plan_request.plan_id == plan.id:
		return "renewal"
	return "plan_change"


def _log_admin_action(actor, action_type, *, details=None, target_user=None, plan_request=None, class_session=None):
	AdminActionLog.objects.create(
		actor=actor,
		action_type=action_type,
		target_user=target_user,
		plan_request=plan_request,
		class_session=class_session,
		details=details,
	)


def _count_teacher_effective_minutes(month_sessions, present_session_ids=None):
	if present_session_ids is None:
		present_session_ids = set(
			ClassAttendance.objects.filter(class_session__in=month_sessions, present=True).values_list(
				"class_session_id",
				flat=True,
			)
		)
	sessions_by_shift = defaultdict(list)
	for session in month_sessions:
		local_start = _get_session_local_datetime(session.starts_at)
		day = local_start.date()
		shift_kind = _get_shift_kind_for_local_start(local_start)
		if shift_kind:
			sessions_by_shift[(day, shift_kind)].append(session)

	total_minutes = 0
	skipped_last_block_count = 0
	for (day, shift_kind), shift_sessions in sessions_by_shift.items():
		shift_sessions.sort(key=lambda s: _get_session_local_datetime(s.starts_at))
		counted_sessions = shift_sessions[:5]
		if counted_sessions and counted_sessions[-1].id not in present_session_ids:
			skipped_last_block_count += 1
		total_minutes += sum(60 for s in counted_sessions if s.id in present_session_ids)

	return total_minutes, skipped_last_block_count


def _build_schedule_context(user, active_plan_request):
	today = timezone.localdate()
	week_start_date = _get_calendar_navigation_start_date(today)
	_ensure_schedule_sessions(week_start_date, DISPLAY_SCHEDULE_DAYS)
	window_start = _to_session_storage_datetime(_combine_local_datetime(week_start_date, time(0, 0)))
	window_end = _to_session_storage_datetime(_combine_local_datetime(week_start_date + timedelta(days=DISPLAY_SCHEDULE_DAYS), time(0, 0)))
	now = timezone.now()
	sessions = list(
		ClassSession.objects.filter(starts_at__gte=window_start, starts_at__lt=window_end)
		.order_by("starts_at")
	)
	capacity_maps = _get_capacity_maps(sessions)
	teachers = list(User.objects.filter(role=UserRole.TEACHER).order_by("nombre", "apellido", "email"))
	years_months = set((_get_session_local_datetime(s.starts_at).year, _get_session_local_datetime(s.starts_at).month) for s in sessions)
	q = models.Q()
	for y, m in years_months:
		q |= models.Q(year=y, month=m)
	monthly_shifts = list(TeacherMonthlyShift.objects.filter(q).select_related("teacher")) if years_months else []
	reservations = capacity_maps["student_reservations"]
	user_reservations = [reservation for reservation in reservations if reservation.user_id == user.id]
	user_reservations_by_session = {reservation.class_session_id: reservation for reservation in user_reservations}

	plan_total_limit = 0
	plan_bonus_count = 0
	plan_used_count = 0
	plan_remaining_count = 0
	if active_plan_request is not None:
		plan_total_limit = _get_plan_total_class_limit(active_plan_request)
		plan_bonus_count = _get_plan_bonus_class_count(user, active_plan_request)
		plan_used_count = _get_plan_used_class_count(user, active_plan_request, now=now)
		plan_remaining_count = max(plan_total_limit + plan_bonus_count - plan_used_count, 0)

	schedule_days = []
	for session in sessions:
		local_start = _get_session_local_datetime(session.starts_at)
		local_end = _get_session_local_datetime(session.ends_at)
		is_booked = session.id in user_reservations_by_session
		if not _is_valid_schedule_slot(local_start, local_end) and not is_booked:
			continue
		day_key = local_start.date()
		if not schedule_days or schedule_days[-1]["date"] != day_key:
			schedule_days.append(
				{
					"date": day_key,
					"weekday": _get_spanish_weekday(local_start),
					"slots": [],
				}
			)

		week_start, _ = _get_week_bounds_from_datetime(session.starts_at)
		can_book, blocked_reason = _plan_allows_booking(active_plan_request, session, now=now)
		total_reservations = capacity_maps["total_by_session"][session.id]
		if can_book and not is_booked and total_reservations >= session.capacidad_maxima:
			can_book = False
			blocked_reason = "Este bloque ya completo sus 4 cupos."

		schedule_days[-1]["slots"].append(
			{
				"session": session,
				"starts_at_local": local_start,
				"ends_at_local": local_end,
				"date_label": _get_spanish_date_label(local_start),
				"time_label": f"{local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}",
				"reservation_count": total_reservations,
				"capacity_left": max(session.capacidad_maxima - total_reservations, 0),
				"is_booked": is_booked,
				"user_reservation": user_reservations_by_session.get(session.id),
				"can_book": can_book,
				"blocked_reason": blocked_reason if not is_booked else "",
				"booking_opens_at": local_start - BOOKING_OPEN_DELTA,
				"booking_opens_at_label": (local_start - BOOKING_OPEN_DELTA).strftime("%d/%m/%Y %H:%M"),
				"plan_total_limit": plan_total_limit,
				"plan_bonus_count": plan_bonus_count,
				"plan_used_count": plan_used_count,
				"plan_remaining_count": plan_remaining_count,
				"single_class_count": len(capacity_maps["single_class_by_session"][session.id]),
				"student_count": len(capacity_maps["student_by_session"][session.id]),
				"time_key": local_start.strftime("%H:%M"),
				"teacher_label": _get_teacher_display_for_session(session, teachers=teachers, monthly_shifts=monthly_shifts),
			}
		)

	calendar_weeks = _build_calendar_weeks(schedule_days)
	return {
		"schedule_days": schedule_days,
		"calendar_weeks": calendar_weeks,
		"default_calendar_week_index": _get_default_calendar_week_index(calendar_weeks),
		"plan_total_limit": plan_total_limit,
		"plan_bonus_count": plan_bonus_count,
		"plan_used_count": plan_used_count,
		"plan_remaining_count": plan_remaining_count,
		"upcoming_reservations_count": len(user_reservations),
		"reservation_form": ClassReservationForm(),
	}


def _format_session_label(class_session):
	local_start = _get_session_local_datetime(class_session.starts_at)
	local_end = _get_session_local_datetime(class_session.ends_at)
	return f"{local_start.strftime('%d/%m/%Y')} de {local_start.strftime('%H:%M')} a {local_end.strftime('%H:%M')}"


def _build_public_single_class_context(selected_session_id=None, booking_form=None):
	today = timezone.localdate()
	week_start_date = _get_calendar_navigation_start_date(today)
	_ensure_schedule_sessions(week_start_date, DISPLAY_SCHEDULE_DAYS)
	window_start = _to_session_storage_datetime(_combine_local_datetime(week_start_date, time(0, 0)))
	window_end = _to_session_storage_datetime(_combine_local_datetime(week_start_date + timedelta(days=DISPLAY_SCHEDULE_DAYS), time(0, 0)))
	now = timezone.now()
	sessions = list(
		ClassSession.objects.filter(starts_at__gte=window_start, starts_at__lt=window_end)
		.order_by("starts_at")
	)
	capacity_maps = _get_capacity_maps(sessions)
	schedule_days = []
	selected_session = next((session for session in sessions if session.id == selected_session_id), None)
	for session in sessions:
		local_start = _get_session_local_datetime(session.starts_at)
		local_end = _get_session_local_datetime(session.ends_at)
		if not _is_valid_schedule_slot(local_start, local_end):
			continue
		day_key = local_start.date()
		if not schedule_days or schedule_days[-1]["date"] != day_key:
			schedule_days.append(
				{
					"date": day_key,
					"weekday": _get_spanish_weekday(local_start),
					"slots": [],
				}
			)

		can_book, blocked_reason = _booking_window_allows_session(session, now=now)
		total_reservations = capacity_maps["total_by_session"][session.id]
		if can_book and total_reservations >= session.capacidad_maxima:
			can_book = False
			blocked_reason = "Este bloque ya completo sus 4 cupos."
		schedule_days[-1]["slots"].append(
			{
				"session": session,
				"starts_at_local": local_start,
				"ends_at_local": local_end,
				"date_label": _get_spanish_date_label(local_start),
				"time_label": f"{local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}",
				"reservation_count": total_reservations,
				"capacity_left": max(session.capacidad_maxima - total_reservations, 0),
				"can_book": can_book,
				"blocked_reason": blocked_reason,
				"is_selected": selected_session_id == session.id,
				"booking_opens_at": local_start - BOOKING_OPEN_DELTA,
				"booking_opens_at_label": (local_start - BOOKING_OPEN_DELTA).strftime("%d/%m/%Y %H:%M"),
				"time_key": local_start.strftime("%H:%M"),
			}
		)

	calendar_weeks = _build_calendar_weeks(schedule_days)
	return {
		"schedule_days": schedule_days,
		"calendar_weeks": calendar_weeks,
		"default_calendar_week_index": _get_default_calendar_week_index(
			calendar_weeks,
			preferred_session_id=selected_session.id if selected_session else None,
		),
		"selected_single_class_session": selected_session,
		"selected_single_class_session_local_start": _get_session_local_datetime(selected_session.starts_at) if selected_session else None,
		"selected_single_class_session_local_end": _get_session_local_datetime(selected_session.ends_at) if selected_session else None,
		"single_class_booking_form": booking_form or SingleClassPublicBookingForm(
			initial={"session_id": selected_session.id} if selected_session else None
		),
		"single_class_plan": PlanCatalog.objects.filter(activo=True, es_clase_suelta=True).first(),
		"transfer_details": TRANSFER_DETAILS,
		"open_single_class_form": selected_session is not None,
	}


def home(request):
	context = {
		"hours_week": "Lunes a viernes: 07:10 - 12:00 y 16:00 - 21:00",
		"hours_saturday": "Sábado: 09:00 - 14:00",
		"location": "Club Cima Pilates, sector oriente de la ciudad",
		"studio_images": [
			{"src": "img/studio-reformer.svg", "title": "Sala Reformer", "text": "Clases guiadas en estaciones individuales."},
			{"src": "img/studio-group.svg", "title": "Espacio de práctica", "text": "Ambiente ordenado para técnica, control y progresión."},
			{"src": "img/studio-cta.svg", "title": "Bienvenida", "text": "Una experiencia visual cálida y minimalista."},
		],
		"benefits": ["Postura", "Movilidad", "Fuerza", "Control", "Respiración"],
		"catalog_plans": list(PlanCatalog.objects.filter(activo=True, es_clase_suelta=False).order_by("orden", "id")),
	}
	single_class_plan = PlanCatalog.objects.filter(activo=True, es_clase_suelta=True).first()
	if single_class_plan and not getattr(single_class_plan, 'descripcion', None):
		single_class_plan.descripcion = "Perfecta para conocer el estudio o asistir de manera flexible cuando lo necesites."
	context["single_class_plan"] = single_class_plan
	return render(request, "core/home.html", context)


@login_required
def dashboard_redirect(request):
	role = request.user.role
	query_string = request.GET.urlencode()
	if role == UserRole.ADMIN:
		target = reverse("core:admin_dashboard")
	elif role in {UserRole.TEACHER, UserRole.RECEPTION}:
		target = reverse("core:teacher_dashboard")
	else:
		target = reverse("core:student_dashboard")
	if query_string:
		target = f"{target}?{query_string}"
	return redirect(target)


@student_required
def student_dashboard(request):
	available_plans = list(PlanCatalog.objects.filter(activo=True).order_by("orden", "id"))
	subscription_plans = [plan for plan in available_plans if not plan.es_clase_suelta]
	all_plan_requests = list(PlanRequest.objects.filter(user=request.user).select_related("plan")[:5])
	current_plan_request = _get_active_plan_request(request.user)
	selected_period = request.GET.get("period", PlanBillingPeriod.MONTHLY)
	if selected_period not in {choice[0] for choice in PlanBillingPeriod.choices}:
		selected_period = PlanBillingPeriod.MONTHLY
	selected_plan = None
	selected_slug = request.GET.get("plan")
	if selected_slug:
		selected_plan = next((plan for plan in subscription_plans if plan.slug == selected_slug), None)
	if selected_plan is None and subscription_plans:
		selected_plan = subscription_plans[0]

	if request.method == "POST":
		plan_request_form = PlanRequestForm(request.POST, request.FILES)
		if plan_request_form.is_valid():
			request_kind = _build_plan_request_kind(request.user, plan_request_form.plan)
			plan_request = plan_request_form.save(request.user)
			send_plan_request_received_email(
				request.user.email,
				request.user.get_full_name() or request.user.email,
				plan_request.plan.nombre,
				plan_request.get_periodo_display(),
				request_kind,
			)
			messages.success(
				request,
				f"Solicitud enviada para {plan_request.plan.nombre}. Te escribiremos por correo cuando el pago sea confirmado.",
			)
			return redirect(f"{reverse('core:student_dashboard')}#solicitud-plan")
		form_selected_slug = plan_request_form.data.get("plan_slug")
		selected_plan = next((plan for plan in subscription_plans if plan.slug == form_selected_slug), selected_plan)
		selected_period = plan_request_form.data.get("periodo", selected_period)
		open_plan_modal = True
	else:
		initial_data = {"periodo": selected_period}
		if selected_plan is not None:
			initial_data["plan_slug"] = selected_plan.slug
		plan_request_form = PlanRequestForm(initial=initial_data)
		open_plan_modal = request.GET.get("open_plan") == "1"

	current_plan_valid_until = None
	current_plan_remaining_label = None
	current_plan_expired = False
	upgrade_plan = None
	if current_plan_request is not None:
		current_plan_valid_until = _get_plan_valid_until(current_plan_request)
		current_plan_remaining_label, current_plan_expired = _format_remaining_time(current_plan_valid_until)
		upgrade_plan = next(
			(plan for plan in subscription_plans if plan.orden > current_plan_request.plan.orden),
			None,
		)

	context = {
		"plans": subscription_plans,
		"single_class_plan": next((plan for plan in available_plans if plan.es_clase_suelta), None),
		"selected_plan": selected_plan,
		"selected_period": selected_period,
		"open_plan_modal": open_plan_modal,
		"plan_request_form": plan_request_form,
		"plan_requests": all_plan_requests,
		"current_plan_request": current_plan_request,
		"current_plan_valid_until": current_plan_valid_until,
		"current_plan_remaining_label": current_plan_remaining_label,
		"current_plan_expired": current_plan_expired,
		"upgrade_plan": upgrade_plan,
		"transfer_details": TRANSFER_DETAILS,
		"plan_total_limit": _get_plan_total_class_limit(current_plan_request) if current_plan_request is not None else 0,
		"plan_bonus_count": _get_plan_bonus_class_count(request.user, current_plan_request) if current_plan_request is not None else 0,
		"plan_used_count": _get_plan_used_class_count(request.user, current_plan_request) if current_plan_request is not None else 0,
	}
	context["plan_remaining_count"] = max(
		context["plan_total_limit"] + context["plan_bonus_count"] - context["plan_used_count"],
		0,
	)
	return render(request, "core/dashboards/student.html", context)


@student_required
def student_schedule(request):
	active_plan_request = _get_active_plan_request(request.user)

	if request.method == "POST":
		action = request.POST.get("action")
		if action == "book":
			reservation_form = ClassReservationForm(request.POST)
			if reservation_form.is_valid():
				try:
					with transaction.atomic():
						class_session = ClassSession.objects.select_for_update().get(pk=reservation_form.cleaned_data["session_id"])
						can_book, blocked_reason = _plan_allows_booking(active_plan_request, class_session)
						if not can_book:
							messages.error(request, blocked_reason)
							return redirect("core:student_schedule")

						existing_reservation = ClassReservation.objects.filter(
							class_session=class_session,
							user=request.user,
						).first()
						if existing_reservation is not None:
							messages.info(request, "Ya estas inscrita en esta clase.")
							return redirect("core:student_schedule")

						allowed_total = _get_plan_total_class_limit(active_plan_request) + _get_plan_bonus_class_count(request.user, active_plan_request)
						used_total = _get_plan_used_class_count(request.user, active_plan_request)
						if used_total >= allowed_total:
							messages.error(request, "Ya alcanzaste el maximo total de clases disponibles para tu plan vigente.")
							return redirect("core:student_schedule")

						current_reservations = (
							ClassReservation.objects.filter(class_session=class_session).count()
							+ SingleClassBooking.objects.filter(
								class_session=class_session,
								estado__in=ACTIVE_SINGLE_CLASS_STATUSES,
							).count()
						)
						if current_reservations >= class_session.capacidad_maxima:
							messages.error(request, "Este bloque ya completo sus 4 cupos disponibles.")
							return redirect("core:student_schedule")

						ClassReservation.objects.create(
							class_session=class_session,
							user=request.user,
							nota=reservation_form.cleaned_data["nota"] or None,
						)
						messages.success(request, "Tu clase quedo reservada correctamente.")
						return redirect("core:student_schedule")
				except IntegrityError:
					messages.error(request, "No fue posible completar la reserva. Intenta nuevamente.")
			else:
				for errors in reservation_form.errors.values():
					for error in errors:
						messages.error(request, error)
		elif action == "cancel":
			reservation_id = request.POST.get("reservation_id")
			try:
				with transaction.atomic():
					reservation = (
						ClassReservation.objects.select_for_update()
						.select_related("class_session")
						.get(pk=reservation_id, user=request.user)
					)
					if _get_session_local_datetime(reservation.class_session.starts_at) <= timezone.now():
						messages.error(request, "No puedes eliminar una clase que ya comenzo.")
					else:
						reservation.delete()
						messages.success(request, "La clase fue eliminada de tu agenda.")
			except (ClassReservation.DoesNotExist, ValueError, TypeError):
				messages.error(request, "No encontramos la reserva que intentas eliminar.")
			return redirect("core:student_schedule")

	context = {
		"active_plan_request": active_plan_request,
	}
	context.update(_build_schedule_context(request.user, active_plan_request))
	return render(request, "core/dashboards/schedule.html", context)


def public_single_class_booking(request):
	selected_session_id = request.GET.get("session")
	try:
		selected_session_id = int(selected_session_id) if selected_session_id else None
	except (TypeError, ValueError):
		selected_session_id = None

	if request.method == "POST":
		booking_form = SingleClassPublicBookingForm(request.POST, request.FILES)
		if booking_form.is_valid():
			try:
				with transaction.atomic():
					class_session = ClassSession.objects.select_for_update().get(pk=booking_form.cleaned_data["session_id"])
					can_book, blocked_reason = _booking_window_allows_session(class_session)
					if not can_book:
						messages.error(request, blocked_reason)
						return redirect("core:public_single_class_booking")

					total_reservations = (
						ClassReservation.objects.filter(class_session=class_session).count()
						+ SingleClassBooking.objects.filter(
							class_session=class_session,
							estado__in=ACTIVE_SINGLE_CLASS_STATUSES,
						).count()
					)
					if total_reservations >= class_session.capacidad_maxima:
						messages.error(request, "Este bloque ya completo sus 4 cupos disponibles.")
						return redirect("core:public_single_class_booking")

					single_class_booking = booking_form.save()
					send_single_class_request_received_email(
						single_class_booking.email,
						f"{single_class_booking.nombre} {single_class_booking.apellido or ''}".strip(),
						_format_session_label(class_session),
						single_class_booking.get_metodo_pago_display(),
					)
					messages.success(
						request,
						"Tu solicitud de clase suelta fue recibida. Te enviaremos un correo con la confirmacion de recepcion.",
					)
					return redirect(f"{reverse('core:public_single_class_booking')}?single_class=ok")
			except IntegrityError:
				messages.error(request, "No fue posible registrar la solicitud. Intenta nuevamente.")
		selected_session_id = booking_form.data.get("session_id")
		try:
			selected_session_id = int(selected_session_id) if selected_session_id else None
		except (TypeError, ValueError):
			selected_session_id = None
	else:
		booking_form = None

	context = {
		"single_class_success": request.GET.get("single_class") == "ok",
	}
	context.update(_build_public_single_class_context(selected_session_id, booking_form=booking_form))
	return render(request, "core/public_single_class_booking.html", context)


def confirm_class_reservation(request, token):
	signer = TimestampSigner(salt="class-reservation-confirm")
	try:
		reservation_id = int(signer.unsign(token, max_age=60 * 60 * 24 * 14))
	except (BadSignature, SignatureExpired, ValueError, TypeError):
		messages.error(request, "El enlace de confirmacion no es valido o expiro.")
		return redirect("core:home")

	try:
		reservation = (
			ClassReservation.objects.select_related("class_session", "user")
			.get(pk=reservation_id)
		)
	except ClassReservation.DoesNotExist:
		messages.error(request, "No encontramos la reserva que intentas confirmar.")
		return redirect("core:home")

	if _get_session_local_datetime(reservation.class_session.starts_at) <= timezone.now():
		messages.error(request, "Esta clase ya comenzo o ya paso.")
		return redirect("core:home")

	reservation.confirmed_at = timezone.now()
	reservation.save(update_fields=["confirmed_at"])
	messages.success(request, "Tu clase fue confirmada correctamente.")
	if request.user.is_authenticated:
		return redirect("core:student_schedule")
	return redirect("core:home")


@teacher_required
def teacher_dashboard(request):
	selected_session_id = request.GET.get("session") or request.POST.get("session_id")
	try:
		selected_session_id = int(selected_session_id) if selected_session_id else None
	except (TypeError, ValueError):
		selected_session_id = None

	selected_month_raw = request.GET.get("month") or request.POST.get("month")
	selected_month_raw = (selected_month_raw or "").strip()
	try:
		selected_month = datetime.strptime(f"{selected_month_raw}-01", "%Y-%m-%d").date().replace(day=1)
	except ValueError:
		selected_month = timezone.localdate().replace(day=1)
	selected_month_str = f"{selected_month.year}-{selected_month.month:02d}"

	if request.method == "POST":
		action = request.POST.get("action")
		if action == "set_month_shifts":
			selected_kinds = [
				value
				for value in request.POST.getlist("shift_kinds")
				if value in {choice[0] for choice in TeacherShiftKind.choices}
			]
			existing = list(
				TeacherMonthlyShift.objects.filter(
					teacher=request.user,
					year=selected_month.year,
					month=selected_month.month,
				)
			)
			existing_by_kind = {item.shift_kind: item for item in existing}
			to_create = [kind for kind in selected_kinds if kind not in existing_by_kind]
			to_delete = [item.id for kind, item in existing_by_kind.items() if kind not in set(selected_kinds)]
			if to_delete:
				TeacherMonthlyShift.objects.filter(id__in=to_delete).delete()
			for kind in to_create:
				TeacherMonthlyShift.objects.create(
					teacher=request.user,
					year=selected_month.year,
					month=selected_month.month,
					shift_kind=kind,
				)
			messages.success(request, "Tu turno mensual quedó actualizado.")
			return redirect(f"{reverse('core:teacher_dashboard')}?month={selected_month_str}")

		if action in {"mark_attendance", "save_teacher_note"}:
			if selected_session_id is None:
				messages.error(request, "Selecciona una clase válida.")
				return redirect(f"{reverse('core:teacher_dashboard')}?month={selected_month_str}")
			class_session = ClassSession.objects.filter(pk=selected_session_id).first()
			if class_session is None or not _teacher_has_access_to_session(request.user, class_session):
				messages.error(request, "No tienes acceso a esa clase desde tu agenda de trabajo.")
				return redirect(f"{reverse('core:teacher_dashboard')}?month={selected_month_str}")

			if action == "mark_attendance":
				present_user_ids = {
					user_id
					for user_id in request.POST.getlist("present_user_ids")
					if user_id
				}
				reservations = list(
					ClassReservation.objects.filter(class_session=class_session).select_related("user")
				)
				for reservation in reservations:
					record = ClassAttendance.objects.filter(
						class_session=class_session,
						user=reservation.user,
					).first()
					is_present = str(reservation.user_id) in present_user_ids
					if record is None:
						ClassAttendance.objects.create(
							class_session=class_session,
							user=reservation.user,
							teacher=request.user,
							present=is_present,
						)
					else:
						record.present = is_present
						record.teacher = request.user
						record.save(update_fields=["present", "teacher", "marked_at"])
				messages.success(request, "La asistencia de la clase quedó actualizada.")
				return redirect(f"{reverse('core:teacher_dashboard')}?month={selected_month_str}&session={class_session.id}#detalle-clase")

			note_value = (request.POST.get("teacher_note") or "").strip()
			note_record = TeacherSessionNote.objects.filter(
				class_session=class_session,
				teacher=request.user,
			).first()
			if note_record is None and note_value:
				TeacherSessionNote.objects.create(
					class_session=class_session,
					teacher=request.user,
					note=note_value,
				)
				messages.success(request, "La nota privada quedó guardada.")
			elif note_record is not None:
				note_record.note = note_value
				note_record.save(update_fields=["note", "updated_at"])
				messages.success(request, "La nota privada fue actualizada.")
			else:
				messages.info(request, "No había contenido para guardar en la nota.")
			return redirect(f"{reverse('core:teacher_dashboard')}?month={selected_month_str}&session={class_session.id}#detalle-clase")

	context = {}
	context.update(
		_build_teacher_schedule_context(
			request.user,
			selected_session_id=selected_session_id,
			selected_month=selected_month,
		)
	)
	return render(request, "core/dashboards/teacher.html", context)

def _build_admin_overview_context():
	today = timezone.localdate()
	week_start_date = _get_calendar_navigation_start_date(today)
	_ensure_schedule_sessions(week_start_date, DISPLAY_SCHEDULE_DAYS)
	window_start = _to_session_storage_datetime(_combine_local_datetime(week_start_date, time(0, 0)))
	window_end = _to_session_storage_datetime(_combine_local_datetime(week_start_date + timedelta(days=DISPLAY_SCHEDULE_DAYS), time(0, 0)))
	sessions = list(ClassSession.objects.filter(starts_at__gte=window_start, starts_at__lt=window_end).order_by("starts_at"))
	
	# Fetch all teachers
	teachers = list(User.objects.filter(role=UserRole.TEACHER).order_by("nombre", "apellido", "email"))
	
	# Month boundaries
	month_start = today.replace(day=1)
	next_month = _add_months(_combine_local_datetime(month_start, time(0, 0)), 1).date()
	month_end = next_month - timedelta(days=1)
	window_start_month = _to_session_storage_datetime(_combine_local_datetime(month_start, time(0, 0)))
	window_end_month = _to_session_storage_datetime(_combine_local_datetime(next_month, time(0, 0)))
	
	# Pre-fetch monthly data once for ALL teachers and global metrics
	prefetch_sessions = list(ClassSession.objects.filter(starts_at__gte=window_start_month, starts_at__lt=window_end_month).order_by("starts_at"))
	prefetch_reservations = list(ClassReservation.objects.filter(class_session__in=prefetch_sessions))
	prefetch_single_bookings = list(SingleClassBooking.objects.filter(class_session__in=prefetch_sessions, estado__in=ACTIVE_SINGLE_CLASS_STATUSES))
	prefetch_attendances = list(ClassAttendance.objects.filter(class_session__in=prefetch_sessions, present=True))
	
	# Calculate total occupied for the entire month
	student_by_session_month = defaultdict(list)
	single_class_by_session_month = defaultdict(list)
	for r in prefetch_reservations:
		student_by_session_month[r.class_session_id].append(r)
	for b in prefetch_single_bookings:
		single_class_by_session_month[b.class_session_id].append(b)
	total_by_session_month = defaultdict(int)
	for s in prefetch_sessions:
		total_by_session_month[s.id] = len(student_by_session_month[s.id]) + len(single_class_by_session_month[s.id])
	
	total_occupied = sum(total_by_session_month[s.id] for s in prefetch_sessions)
	
	# Calculate theoretical month capacity based on weekdays, Saturdays, and holidays
	total_capacity = 0
	current_day = month_start
	while current_day <= month_end:
		if holidays_cl.is_holiday(current_day) or current_day.weekday() == 6:
			pass
		elif current_day.weekday() == 5:
			total_capacity += 20 # 5 classes * 4 capacity
		else:
			total_capacity += 40 # 10 classes * 4 capacity
		current_day += timedelta(days=1)
		
	# Deduct blocked sessions capacity
	blocked_capacity_month = sum(s.capacidad_maxima for s in prefetch_sessions if s.is_blocked)
	total_capacity = max(total_capacity - blocked_capacity_month, 0)
	
	now = timezone.now()
	past_sessions_month = []
	for s in prefetch_sessions:
		dt = s.starts_at
		if timezone.is_naive(dt):
			dt = timezone.make_aware(dt, dt_timezone.utc)
		now_aware = now if not timezone.is_naive(now) else timezone.make_aware(now, dt_timezone.utc)
		if dt <= now_aware:
			past_sessions_month.append(s)
			
	past_occupied = sum(total_by_session_month[s.id] for s in past_sessions_month)
	past_session_ids = {s.id for s in past_sessions_month}
	present_attendance_count = sum(1 for a in prefetch_attendances if a.class_session_id in past_session_ids)
	
	# Shifts dictionary mapping teacher_id to set of shift kinds
	prefetch_shifts = defaultdict(set)
	for s in TeacherMonthlyShift.objects.filter(year=month_start.year, month=month_start.month):
		prefetch_shifts[s.teacher_id].add(s.shift_kind)
		
	# Adjustments dict mapping teacher_id to sum of minutes_delta
	prefetch_adjustments = defaultdict(int)
	adjustments_qs = TeacherHoursAdjustment.objects.filter(year=month_start.year, month=month_start.month).values("teacher_id").annotate(total_delta=models.Sum("minutes_delta"))
	for adj in adjustments_qs:
		prefetch_adjustments[adj["teacher_id"]] = adj["total_delta"] or 0
		
	# Build the prefetch_data dictionary
	prefetch_data = {
		"sessions": prefetch_sessions,
		"reservations": prefetch_reservations,
		"single_bookings": prefetch_single_bookings,
		"attendances": prefetch_attendances,
		"shifts": prefetch_shifts,
		"adjustments": prefetch_adjustments,
	}
	
	teacher_month_summaries = [
		{
			"teacher": teacher,
			"metrics": _build_teacher_month_metrics(teacher, target_month=today, prefetch_data=prefetch_data),
		}
		for teacher in teachers
	]
	return {
		"dashboard_session_count": len(prefetch_sessions),
		"dashboard_total_capacity": total_capacity,
		"dashboard_total_occupied": total_occupied,
		"dashboard_occupancy_rate": (total_occupied / total_capacity) if total_capacity else 0,
		"dashboard_occupancy_percent": round((total_occupied / total_capacity) * 100) if total_capacity else 0,
		"dashboard_attendance_rate": (present_attendance_count / past_occupied) if past_occupied else 0,
		"dashboard_attendance_percent": round((present_attendance_count / past_occupied) * 100) if past_occupied else 0,
		"dashboard_present_attendance_count": present_attendance_count,
		"dashboard_total_occupied_past": past_occupied,
		"dashboard_blocked_session_count": sum(1 for session in prefetch_sessions if session.is_blocked),
		"dashboard_teacher_summary_count": len(teacher_month_summaries),
		"teacher_month_summaries": teacher_month_summaries,
	}
@login_required
@admin_required
def admin_dashboard(request):
	if request.method == "POST":
		action = request.POST.get("action")
		if action in {"confirm_plan", "reject_plan"}:
			try:
				plan_request_id = int(request.POST.get("plan_request_id") or "")
			except (TypeError, ValueError):
				plan_request_id = None
			if not plan_request_id:
				messages.error(request, "No encontramos la solicitud seleccionada.")
				return redirect("core:admin_dashboard")
			try:
				with transaction.atomic():
					plan_request = PlanRequest.objects.select_for_update().get(pk=plan_request_id)
					if action == "confirm_plan":
						plan_request.estado = PlanRequestStatus.CONFIRMED
						plan_request.save(update_fields=["estado", "updated_at"])
						_log_admin_action(
							request.user,
							AdminActionType.PLAN_CONFIRMED,
							target_user=plan_request.user,
							plan_request=plan_request,
							details=f"{plan_request.plan.nombre} · {plan_request.get_periodo_display()}",
						)
						messages.success(request, "La solicitud fue confirmada y el plan quedó vigente.")
					else:
						plan_request.estado = PlanRequestStatus.REJECTED
						plan_request.save(update_fields=["estado", "updated_at"])
						_log_admin_action(
							request.user,
							AdminActionType.PLAN_REJECTED,
							target_user=plan_request.user,
							plan_request=plan_request,
							details=f"{plan_request.plan.nombre} · {plan_request.get_periodo_display()}",
						)
						messages.success(request, "La solicitud fue rechazada.")
			except PlanRequest.DoesNotExist:
				messages.error(request, "No encontramos la solicitud seleccionada.")
			return redirect("core:admin_dashboard")

		if action == "add_bonus_classes":
			email = (request.POST.get("student_email") or "").strip().lower()
			motivo = (request.POST.get("motivo") or "").strip() or None
			try:
				cantidad = int(request.POST.get("cantidad") or "0")
			except (TypeError, ValueError):
				cantidad = 0
			if not email or cantidad == 0:
				messages.error(request, "Ingresa el correo de la alumna y una cantidad válida distinta de 0.")
				return redirect("core:admin_dashboard")
			student = User.objects.filter(email__iexact=email).first()
			if student is None:
				messages.error(request, "No encontramos una alumna con ese correo.")
				return redirect("core:admin_dashboard")
			active_plan = _get_active_plan_request(student)
			if active_plan is None:
				messages.error(request, "La alumna no tiene un plan vigente confirmado.")
				return redirect("core:admin_dashboard")
			adjustment = ClassCreditAdjustment.objects.create(
				user=student,
				plan_request=active_plan,
				cantidad=cantidad,
				motivo=motivo,
			)
			if cantidad > 0:
				detail_str = f"+{cantidad} clases"
				success_msg = f"Se agregaron {cantidad} clases adicionales a la cuenta de la alumna."
			else:
				detail_str = f"{cantidad} clases"
				success_msg = f"Se descontaron {abs(cantidad)} clases de la cuenta de la alumna."
			_log_admin_action(
				request.user,
				AdminActionType.BONUS_CLASSES_ADDED,
				target_user=student,
				plan_request=active_plan,
				details=detail_str,
			)
			messages.success(request, success_msg)
			return redirect("core:admin_dashboard")

		if action == "adjust_teacher_hours":
			teacher_email = (request.POST.get("teacher_email") or "").strip().lower()
			month_raw = (request.POST.get("month") or "").strip()
			reason = (request.POST.get("reason") or "").strip() or None
			try:
				hours_delta = int(request.POST.get("hours_delta") or "0")
			except (TypeError, ValueError):
				hours_delta = 0
			if not teacher_email or not month_raw or hours_delta == 0:
				messages.error(request, "Ingresa el correo de la profesora, el mes y un ajuste distinto de 0.")
				return redirect("core:admin_dashboard")
			try:
				month_date = datetime.strptime(f"{month_raw}-01", "%Y-%m-%d").date()
			except ValueError:
				messages.error(request, "El mes no es válido.")
				return redirect("core:admin_dashboard")
			teacher = User.objects.filter(email__iexact=teacher_email, role=UserRole.TEACHER).first()
			if teacher is None:
				messages.error(request, "No encontramos una profesora con ese correo.")
				return redirect("core:admin_dashboard")
			adjustment = TeacherHoursAdjustment.objects.create(
				teacher=teacher,
				year=month_date.year,
				month=month_date.month,
				minutes_delta=hours_delta * 60,
				reason=reason,
			)
			_log_admin_action(
				request.user,
				AdminActionType.TEACHER_HOURS_ADJUSTED,
				target_user=teacher,
				details=f"{adjustment.year}-{adjustment.month:02d}: {adjustment.minutes_delta} min",
			)
			messages.success(request, "El ajuste de horas fue registrado.")
			return redirect("core:admin_dashboard")

	pending_plan_requests = list(
		PlanRequest.objects.filter(estado__in=(PlanRequestStatus.PENDING, PlanRequestStatus.UNDER_REVIEW))
		.select_related("user", "plan")
		.order_by("-created_at")[:25]
	)
	recent_confirmed_plans = list(
		PlanRequest.objects.filter(estado=PlanRequestStatus.CONFIRMED)
		.select_related("user", "plan")
		.order_by("-created_at")[:10]
	)
	recent_adjustments = list(
		ClassCreditAdjustment.objects.select_related("user", "plan_request")
		.order_by("-created_at")[:20]
	)
	recent_teacher_notes = list(
		TeacherSessionNote.objects.select_related("teacher", "class_session")
		.order_by("-updated_at")[:12]
	)
	recent_teacher_hour_adjustments = list(
		TeacherHoursAdjustment.objects.select_related("teacher").order_by("-created_at")[:20]
	)
	recent_admin_actions = list(
		AdminActionLog.objects.select_related("actor", "target_user", "plan_request", "class_session")
		.order_by("-created_at")[:20]
	)
	plan_approval_history = list(
		AdminActionLog.objects.filter(
			action_type__in=(AdminActionType.PLAN_CONFIRMED, AdminActionType.PLAN_REJECTED)
		)
		.select_related("actor", "target_user", "plan_request")
		.order_by("-created_at")[:12]
	)
	context = {
		"pending_plan_requests": pending_plan_requests,
		"recent_confirmed_plans": recent_confirmed_plans,
		"recent_adjustments": recent_adjustments,
		"recent_teacher_notes": recent_teacher_notes,
		"recent_teacher_hour_adjustments": recent_teacher_hour_adjustments,
		"recent_admin_actions": recent_admin_actions,
		"plan_approval_history": plan_approval_history,
	}
	context.update(_build_admin_overview_context())
	return render(request, "core/dashboards/admin.html", context)


@login_required
@admin_required
def admin_schedule_view(request):
	import json
	today = timezone.localdate()
	week_start_date = _get_calendar_navigation_start_date(today)
	_ensure_schedule_sessions(week_start_date, DISPLAY_SCHEDULE_DAYS)
	window_start = _to_session_storage_datetime(_combine_local_datetime(week_start_date, time(0, 0)))
	window_end = _to_session_storage_datetime(_combine_local_datetime(week_start_date + timedelta(days=DISPLAY_SCHEDULE_DAYS), time(0, 0)))

	if request.method == "POST":
		action = request.POST.get("action")
		if action == "admin_book_user":
			email = (request.POST.get("user_email") or "").strip().lower()
			nota = (request.POST.get("nota") or "").strip() or None
			try:
				session_id = int(request.POST.get("session_id") or "")
			except (TypeError, ValueError):
				session_id = None
			if not email or session_id is None:
				messages.error(request, "Ingresa un correo y una clase válidos.")
				return redirect("core:admin_schedule")
			student = User.objects.filter(email__iexact=email).first()
			if student is None:
				messages.error(request, "No encontramos una usuaria con ese correo.")
				return redirect("core:admin_schedule")
			try:
				with transaction.atomic():
					class_session = ClassSession.objects.select_for_update().get(pk=session_id)
					if class_session.is_blocked:
						messages.error(request, class_session.blocked_reason or "La clase está bloqueada por administración.")
						return redirect("core:admin_schedule")
					if ClassReservation.objects.filter(class_session=class_session, user=student).exists():
						messages.info(request, "La usuaria ya está agendada en esta clase.")
						return redirect("core:admin_schedule")
					current_occupancy = ClassReservation.objects.filter(class_session=class_session).count() + SingleClassBooking.objects.filter(
						class_session=class_session,
						estado__in=ACTIVE_SINGLE_CLASS_STATUSES,
					).count()
					if current_occupancy >= class_session.capacidad_maxima:
						messages.error(request, "Este bloque ya completó sus cupos.")
						return redirect("core:admin_schedule")
					reservation = ClassReservation.objects.create(class_session=class_session, user=student, nota=nota)
					_log_admin_action(
						request.user,
						AdminActionType.CLASS_BOOKED,
						target_user=student,
						class_session=class_session,
						details=nota or f"Reserva manual #{reservation.id}",
					)
					messages.success(request, "La usuaria quedó agendada en la clase.")
			except ClassSession.DoesNotExist:
				messages.error(request, "No encontramos la clase seleccionada.")
			return redirect("core:admin_schedule")

		if action in {"block_class", "unblock_class"}:
			try:
				session_id = int(request.POST.get("session_id") or "")
			except (TypeError, ValueError):
				session_id = None
			blocked_reason = (request.POST.get("blocked_reason") or "").strip() or None
			if session_id is None:
				messages.error(request, "No encontramos la clase seleccionada.")
				return redirect("core:admin_schedule")
			try:
				with transaction.atomic():
					class_session = ClassSession.objects.select_for_update().get(pk=session_id)
					if action == "block_class":
						class_session.is_blocked = True
						class_session.blocked_reason = blocked_reason or "Bloqueado por administración."
						class_session.save(update_fields=["is_blocked", "blocked_reason", "updated_at"])
						_log_admin_action(
							request.user,
							AdminActionType.CLASS_BLOCKED,
							class_session=class_session,
							details=class_session.blocked_reason,
						)
						messages.success(request, "La clase fue bloqueada.")
					else:
						class_session.is_blocked = False
						class_session.blocked_reason = None
						class_session.save(update_fields=["is_blocked", "blocked_reason", "updated_at"])
						_log_admin_action(
							request.user,
							AdminActionType.CLASS_UNBLOCKED,
							class_session=class_session,
							details="Bloque liberado por administración.",
						)
						messages.success(request, "La clase fue desbloqueada.")
			except ClassSession.DoesNotExist:
				messages.error(request, "No encontramos la clase seleccionada.")
			return redirect("core:admin_schedule")

	sessions = list(ClassSession.objects.filter(starts_at__gte=window_start, starts_at__lt=window_end).order_by("starts_at"))
	capacity_maps = _get_capacity_maps(sessions)
	teachers = list(User.objects.filter(role=UserRole.TEACHER).order_by("nombre", "apellido", "email"))
	years_months = set((_get_session_local_datetime(s.starts_at).year, _get_session_local_datetime(s.starts_at).month) for s in sessions)
	q = models.Q()
	for y, m in years_months:
		q |= models.Q(year=y, month=m)
	monthly_shifts = list(TeacherMonthlyShift.objects.filter(q).select_related("teacher")) if years_months else []
	attendance_records = list(
		ClassAttendance.objects.filter(class_session__in=sessions, present=True).select_related("user", "teacher")
	)
	attendance_by_session = defaultdict(list)
	for record in attendance_records:
		attendance_by_session[record.class_session_id].append(record)

	schedule_days = []
	for session in sessions:
		local_start = _get_session_local_datetime(session.starts_at)
		local_end = _get_session_local_datetime(session.ends_at)
		reservation_count = capacity_maps["total_by_session"][session.id]
		if not _is_valid_schedule_slot(local_start, local_end) and reservation_count == 0:
			continue
		day_key = local_start.date()
		if not schedule_days or schedule_days[-1]["date"] != day_key:
			schedule_days.append(
				{
					"date": day_key,
					"weekday": _get_spanish_weekday(local_start),
					"slots": [],
				}
			)
		student_reservations = capacity_maps["student_by_session"][session.id]
		single_bookings = capacity_maps["single_class_by_session"][session.id]
		present_records = attendance_by_session[session.id]
		reservation_count = capacity_maps["total_by_session"][session.id]
		total_capacity = session.capacidad_maxima or 0

		attendees = []
		for r in student_reservations:
			attendees.append({
				"id": r.id,
				"type": "regular",
				"name": r.user.get_full_name() or r.user.email,
				"email": r.user.email,
			})
		for b in single_bookings:
			from django.conf import settings
			attendees.append({
				"id": b.id,
				"type": "single",
				"name": f"{b.nombre} {b.apellido or ''}".strip(),
				"email": b.email,
				"estado": b.estado,
				"comprobante_url": settings.MEDIA_URL + b.comprobante_path if b.comprobante_path else None,
			})

		schedule_days[-1]["slots"].append(
			{
				"session": session,
				"starts_at_local": local_start,
				"ends_at_local": local_end,
				"date_label": _get_spanish_date_label(local_start),
				"time_label": f"{local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}",
				"reservation_count": reservation_count,
				"attendance_count": len(present_records),
				"attendance_rate": (len(present_records) / reservation_count) if reservation_count else 0,
				"capacity_left": max(total_capacity - reservation_count, 0),
				"student_names": [reservation.user.get_full_name() or reservation.user.email for reservation in student_reservations] + [f"{b.nombre} {b.apellido or ''} (Clase Suelta)".strip() for b in single_bookings],
				"present_names": [record.user.get_full_name() or record.user.email for record in present_records],
				"teacher_label": _get_teacher_display_for_session(session, teachers=teachers, monthly_shifts=monthly_shifts),
				"is_blocked": session.is_blocked,
				"blocked_reason": session.blocked_reason or "",
				"time_key": local_start.strftime("%H:%M"),
				"attendees_json": json.dumps(attendees),
			}
		)

	calendar_weeks = _build_calendar_weeks(schedule_days)
	visible_sessions = []
	for day in schedule_days:
		for slot in day["slots"]:
			visible_sessions.append(slot["session"])
	
	total_sessions_count = len(visible_sessions)
	blocked_sessions_count = sum(1 for s in visible_sessions if s.is_blocked)

	return render(
		request,
		"core/dashboards/admin_schedule.html",
		{
			"calendar_weeks": calendar_weeks,
			"default_calendar_week_index": _get_default_calendar_week_index(calendar_weeks),
			"schedule_days": schedule_days,
			"blocked_sessions_count": blocked_sessions_count,
			"total_sessions_count": total_sessions_count,
		},
	)


@login_required
@admin_required
def admin_plan_pricing_view(request):
	if request.method == "POST" and request.POST.get("action") == "update_plan_prices":
		try:
			plan_id = int(request.POST.get("plan_id") or "")
		except (TypeError, ValueError):
			plan_id = None
		if plan_id is None:
			messages.error(request, "No encontramos el plan seleccionado.")
			return redirect("core:admin_plan_pricing")
		try:
			with transaction.atomic():
				plan = PlanCatalog.objects.select_for_update().get(pk=plan_id)
				plan.precio_mensual = int(request.POST.get("precio_mensual") or plan.precio_mensual)
				plan.precio_trimestral = int(request.POST.get("precio_trimestral") or plan.precio_trimestral)
				plan.precio_semestral = int(request.POST.get("precio_semestral") or plan.precio_semestral)
				plan.save(update_fields=["precio_mensual", "precio_trimestral", "precio_semestral", "updated_at"])
				_log_admin_action(
					request.user,
					AdminActionType.PLAN_PRICE_UPDATED,
					details=f"{plan.nombre}: {plan.precio_mensual} / {plan.precio_trimestral} / {plan.precio_semestral}",
				)
				messages.success(request, f"Los precios de {plan.nombre} fueron actualizados.")
		except (PlanCatalog.DoesNotExist, ValueError):
			messages.error(request, "No pudimos guardar los precios del plan.")
		return redirect("core:admin_plan_pricing")

	plans = list(PlanCatalog.objects.order_by("orden", "id"))
	return render(
		request,
		"core/dashboards/admin_plans.html",
		{
			"plans": plans,
			"recent_price_updates": list(
				AdminActionLog.objects.filter(action_type=AdminActionType.PLAN_PRICE_UPDATED)
				.select_related("actor")
				.order_by("-created_at")[:12]
			),
		},
	)


@login_required
@admin_required
def admin_remove_attendee(request):
	if request.method == "POST":
		session_id = request.POST.get("session_id")
		attendee_id = request.POST.get("attendee_id")
		attendee_type = request.POST.get("attendee_type")
		descontar_clase = request.POST.get("descontar_clase") == "1"

		if not session_id or not attendee_id or not attendee_type:
			messages.error(request, "Parámetros insuficientes.")
			return redirect("core:admin_schedule")

		try:
			session_id = int(session_id)
			attendee_id = int(attendee_id)
		except ValueError:
			messages.error(request, "Identificadores inválidos.")
			return redirect("core:admin_schedule")

		try:
			with transaction.atomic():
				class_session = ClassSession.objects.select_for_update().get(pk=session_id)
				if attendee_type == "regular":
					reservation = ClassReservation.objects.select_for_update().select_related("user").get(pk=attendee_id, class_session=class_session)
					user = reservation.user
					starts_at_local = _get_session_local_datetime(class_session.starts_at)
					starts_at_formatted = starts_at_local.strftime("%d/%m/%Y %H:%M")

					# If descontar_clase is True, they lose the class credit (remains deducted)
					if descontar_clase:
						active_plan_request = _get_active_plan_request(user)
						ClassCreditAdjustment.objects.create(
							user=user,
							plan_request=active_plan_request,
							cantidad=-1,
							motivo=f"Clase descontada tras ser removido/a de la clase del {starts_at_formatted} por administración."
						)
						messages.success(request, f"{user.get_full_name() or user.email} fue removida/o de la clase. La clase fue descontada de su plan.")
					else:
						messages.success(request, f"{user.get_full_name() or user.email} fue removida/o de la clase. La clase no fue descontada (crédito devuelto).")

					reservation.delete()

					_log_admin_action(
						request.user,
						AdminActionType.CLASS_REMOVED,
						target_user=user,
						class_session=class_session,
						details=f"Removida/o de la clase. Descontar clase: {'Sí' if descontar_clase else 'No'}"
					)

				elif attendee_type == "single":
					booking = SingleClassBooking.objects.select_for_update().get(pk=attendee_id, class_session=class_session)
					name = f"{booking.nombre} {booking.apellido or ''}".strip()
					booking.delete()
					messages.success(request, f"Clase suelta de {name} fue removida de la clase.")

					_log_admin_action(
						request.user,
						AdminActionType.CLASS_REMOVED,
						class_session=class_session,
						details=f"Removida clase suelta de {name}."
					)
				else:
					messages.error(request, "Tipo de asistente desconocido.")

		except ClassSession.DoesNotExist:
			messages.error(request, "No se encontró la clase seleccionada.")
		except (ClassReservation.DoesNotExist, SingleClassBooking.DoesNotExist):
			messages.error(request, "No se encontró la reserva o clase suelta seleccionada.")
		except Exception as e:
			messages.error(request, f"Ocurrió un error: {str(e)}")

	return redirect("core:admin_schedule")


@login_required
@admin_required
def admin_confirm_single_class_payment(request):
	if request.method == "POST":
		session_id = request.POST.get("session_id")
		booking_id = request.POST.get("booking_id")

		if not session_id or not booking_id:
			messages.error(request, "Parámetros insuficientes.")
			return redirect("core:admin_schedule")

		try:
			session_id = int(session_id)
			booking_id = int(booking_id)
		except ValueError:
			messages.error(request, "Identificadores inválidos.")
			return redirect("core:admin_schedule")

		try:
			with transaction.atomic():
				booking = SingleClassBooking.objects.select_for_update().get(pk=booking_id, class_session_id=session_id)
				
				# Send confirmation email
				from .emails import send_single_class_confirmed_email
				send_single_class_confirmed_email(
					booking.email,
					f"{booking.nombre} {booking.apellido or ''}".strip(),
					_format_session_label(booking.class_session),
				)
				
				if booking.estado == SingleClassBookingStatus.CONFIRMED:
					messages.success(request, f"Correo de confirmación reenviado a {booking.nombre}.")
				else:
					booking.estado = SingleClassBookingStatus.CONFIRMED
					booking.save(update_fields=["estado", "updated_at"])
					
					_log_admin_action(
						request.user,
						AdminActionType.CLASS_BOOKED,
						class_session=booking.class_session,
						details=f"Confirmada clase suelta de {booking.nombre} {booking.apellido or ''}.",
					)
					messages.success(request, f"Pago aprobado y correo de confirmación enviado a {booking.nombre}.")
		except SingleClassBooking.DoesNotExist:
			messages.error(request, "No se encontró la solicitud de clase suelta.")
		except Exception as e:
			messages.error(request, f"Ocurrió un error: {str(e)}")

	return redirect("core:admin_schedule")

