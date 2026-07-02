from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def _send_email(subject, to_email, text_template, html_template, context, fail_silently=True):
    if not to_email:
        return

    text_body = render_to_string(text_template, context)
    html_body = render_to_string(html_template, context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
        reply_to=[settings.REPLY_TO_EMAIL] if settings.REPLY_TO_EMAIL else None,
        bcc=[settings.BOOKING_NOTIFICATION_EMAIL] if settings.BOOKING_NOTIFICATION_EMAIL else None,
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=fail_silently)


def send_plan_request_received_email(email, full_name, plan_name, period_label, request_kind, fail_silently=True):
    subject_map = {
        "new_plan": "Recibimos tu solicitud de plan en Cima Pilates",
        "renewal": "Recibimos tu solicitud de renovacion en Cima Pilates",
        "plan_change": "Recibimos tu solicitud de cambio de plan en Cima Pilates",
    }
    template_map = {
        "new_plan": "emails/plan_request_received",
        "renewal": "emails/plan_renewal_received",
        "plan_change": "emails/plan_change_received",
    }
    template_base = template_map.get(request_kind, "emails/plan_request_received")
    context = {
        "full_name": full_name,
        "plan_name": plan_name,
        "period_label": period_label,
        "site_url": settings.SITE_URL,
        "reply_to_email": settings.REPLY_TO_EMAIL,
    }
    _send_email(
        subject_map.get(request_kind, subject_map["new_plan"]),
        email,
        f"{template_base}.txt",
        f"{template_base}.html",
        context,
        fail_silently=fail_silently,
    )


def send_single_class_request_received_email(email, full_name, class_datetime_label, payment_method_label, fail_silently=True):
    context = {
        "full_name": full_name,
        "class_datetime_label": class_datetime_label,
        "payment_method_label": payment_method_label,
        "site_url": settings.SITE_URL,
        "reply_to_email": settings.REPLY_TO_EMAIL,
    }
    _send_email(
        "Recibimos tu solicitud de clase suelta en Cima Pilates",
        email,
        "emails/single_class_request_received.txt",
        "emails/single_class_request_received.html",
        context,
        fail_silently=fail_silently,
    )


def send_class_reservation_confirmation_request_email(email, full_name, class_datetime_label, confirm_url, fail_silently=True):
    context = {
        "full_name": full_name,
        "class_datetime_label": class_datetime_label,
        "confirm_url": confirm_url,
        "site_url": settings.SITE_URL,
        "reply_to_email": settings.REPLY_TO_EMAIL,
    }
    _send_email(
        "Confirma tu asistencia a tu clase en Cima Pilates",
        email,
        "emails/class_reservation_confirmation_request.txt",
        "emails/class_reservation_confirmation_request.html",
        context,
        fail_silently=fail_silently,
    )
