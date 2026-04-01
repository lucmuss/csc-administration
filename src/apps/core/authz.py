from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def role_required(check, denied_message):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = getattr(request, "user", None)
            if not getattr(user, "is_authenticated", False):
                return redirect_to_login(request.get_full_path())
            if not check(user):
                messages.info(request, denied_message)
                return redirect("core:dashboard")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def staff_or_board_required(check):
    return role_required(check, "Dieser Bereich ist nur fuer Mitarbeitende und Vorstand verfuegbar.")


def board_required(check):
    return role_required(check, "Dieser Bereich ist nur fuer den Vorstand verfuegbar.")
