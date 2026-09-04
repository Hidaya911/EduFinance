from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


ROLE_SUPER_ADMIN = "Super Administrator"
ROLE_SCHOOL_ADMIN = "School Administrator"
ROLE_ACCOUNTANT = "Accountant"
ROLE_CASHIER = "Cashier"
ROLE_AUDITOR = "Auditor"


def user_has_role(user, allowed_roles):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(
        name__in=allowed_roles
    ).exists()


def roles_required(*allowed_roles):
    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not user_has_role(
                request.user,
                allowed_roles,
            ):
                raise PermissionDenied

            return view_func(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator