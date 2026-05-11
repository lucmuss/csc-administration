from django.conf import settings


def is_overadmin(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    email = (getattr(user, "email", "") or "").strip().lower()
    return bool(email and email in getattr(settings, "OVERADMIN_EMAILS", set()))
