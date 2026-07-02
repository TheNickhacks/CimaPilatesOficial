from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import UserRole


def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied("No tienes permisos para acceder a esta sección")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


admin_required = role_required(UserRole.ADMIN)
reception_required = role_required(UserRole.RECEPTION, UserRole.ADMIN)
teacher_required = role_required(UserRole.TEACHER, UserRole.ADMIN, UserRole.RECEPTION)
student_required = role_required(UserRole.STUDENT)
